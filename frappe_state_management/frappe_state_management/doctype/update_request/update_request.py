# -*- coding: utf-8 -*-
# Copyright (c) 2020, Leam Technology Systems and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

from datetime import datetime

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
  approved_on: datetime
  rejected_by: str
  rejected_on: datetime
  revert_items: list
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
      frappe.throw(_("Docfield type must be selected"), ValidationError)

  def before_insert(self):
    """
    Make sure that the status and other fields are set correctly
    :return:
    """
    if self.status != 'Pending':
      self.status = 'Pending'
    if self.error:
      self.error = ''
    if self.revert_items:
      self.revert_items = []
    if self.approved_by:
      self.approval_party = ''
    if self.approved_on:
      self.approved_on = None
    if self.rejected_by:
      self.rejected_by = ''
    if self.approved_by:
      self.approved_by = ''
    if self.approved_on:
      self.rejected_on = None

  def on_submit(self):
    """
    Applies the update on the target doctype by calling the `apply_update_request`
    :return:
    """
    self.apply_update_request()

  def on_update_after_submit(self):
    """
    In case the update request is approved, apply the update request
    :return:
    """
    if self.status == 'Approved':
      self.apply_update_request()

  def apply_update_request(self):
    """
    Applies the update request by calling `FSMDocument` apply_update_request
    :return:
    """
    doc = frappe.get_doc(self.dt, self.docname)
    getattr(doc, 'apply_update_request')(self)
