# -*- coding: utf-8 -*-
# Copyright (c) 2020, Leam Technology Systems and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _, ValidationError
from frappe.model.document import Document
from frappe_state_management.classes.fsm_error import PendingUpdateRequestError


class UpdateRequest(Document):
  status: str
  dt: str
  docname: str
  docfield: str
  type: str
  data: str
  custom_call: str
  party_type: str
  approval_party: str
  approved_by: str
  revert_data: str
  error: str

  def validate(self):

    # Check if the target doctype is a child doctype
    meta = frappe.get_meta(self.dt)
    if meta.istable:
      frappe.throw(_("Child DocTypes not allowed"))

    # Check if the target doctype extends FSMDocument
    from frappe_state_management.classes.fsm_document import FSMDocument
    doc = frappe.get_doc(self.dt, self.docname)
    if not isinstance(doc, FSMDocument):
      frappe.throw(_("Target DocType does not extend FSMDocument"), ValidationError)

    # Check if existing Pending Update Request exist
    if len(frappe.get_all('Update Request', filters={"dt": self.dt, "docname": self.docname, "docstatus": 1,
                                                     "status": ['in', ['Pending', 'Pending Approval']]})) > 0:
      raise PendingUpdateRequestError

    # Check if either docfield or custom call is specified
    if not self.docfield and not self.custom_call:
      frappe.throw(_("Either docfield or Custom Call should be specified"), ValidationError)

    if self.docfield and not self.type:
      frappe.throw(_("Docfield update "), ValidationError)

  def on_submit(self):
    """
    Applies the update on the target doctype by calling the `apply_update_request`
    :return:
    """
    doc = frappe.get_doc(self.dt, self.docname)
    getattr(doc, 'apply_update_request')(self, self.data)
