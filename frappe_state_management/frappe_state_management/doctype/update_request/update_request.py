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
  request_type: str
  dt: str
  docname: str
  created_docname: str
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

    # Check if existing Pending Update Request exist
    requests = frappe.get_all('Update Request',
                              filters=[["dt", "=", self.dt], ["docstatus", "=", 1], ['docname', '!=', None],
                                       ['docname', '=', self.docname],
                                       ["status", "IN", ['Pending', 'Pending Approval']]])

    if len(requests) > 0:
      raise PendingUpdateRequestError

    if self.request_type != 'Create':

      # Check if the target doctype extends FSMDocument
      from frappe_state_management.classes.fsm_document import FSMDocument
      doc = frappe.get_doc(self.dt, self.docname)
      if not isinstance(doc, FSMDocument):
        frappe.throw(_("Target DocType does not extend FSMDocument"), ValidationError)

      # Check if either docfield or custom call is specified
      if not self.docfield and not self.custom_call:
        frappe.throw(_("Either docfield or Custom Call should be specified"), ValidationError)

      if self.docfield and not self.type:
        frappe.throw(_("Docfield type must be selected"), ValidationError)
    else:
      if not self.data or not isinstance(frappe.parse_json(self.data), frappe._dict):
        frappe.throw(_("Invalid Data field, make sure it's a JSON object"), ValidationError)

  def before_insert(self):
    """
    Make sure that the status and other fields are set correctly
    :return:
    """
    if self.status != 'Pending':
      self.status = 'Pending'
    self.created_docname = ''
    self.error = ''
    self.revert_items = []
    self.approval_party = ''
    self.approved_by = ''
    self.approved_on = None
    self.rejected_by = ''
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

    if self.request_type != 'Create':
      doc = frappe.get_doc(self.dt, self.docname)
      getattr(doc, 'apply_update_request')(self)
    else:
      doc = frappe.get_doc(frappe.parse_json(self.data))
      getattr(doc, 'create_document')(self)

  def revert(self):
    """
    Calls the revert function of the document.
    Validates before applying the revert
    :return:
    """
    self.validate_revert()

    doc = frappe.get_doc(self.dt, self.docname)
    getattr(doc, 'revert')(self)

  def validate_revert(self):
    """
    Validates the conditions before applying the revert
    1- Must be a Successful update request
    2- Must be the last Successful update request
    :return:
    """
    # Check if the Update Request is successful
    if self.status != 'Success':
      frappe.throw("Update Request is not marked as successful")

    # Check if the update request is the latest
    prev = frappe.get_all("Update Request", filters={'status': 'Success', 'dt': self.dt, 'docname': self.docname},
                          order_by='modified_date DESC')

    if len(prev) and prev[0].name == self.name:
      return

    frappe.throw("Not the latest Successful Update Request")
