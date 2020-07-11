import frappe
from frappe.utils import now_datetime
from frappe_state_management.frappe_state_management.doctype.update_request.update_request import UpdateRequest

dt = 'Update Request'


@frappe.whitelist()
def approve(update_request: str) -> dict:
  """
  Approve an update request.
  :param update_request: The update request's name that will be approved
  :return:
  """
  user = frappe.session.user

  update_request_doc: UpdateRequest = frappe.get_doc(dt, update_request)
  update_request_doc.status = 'Approved'
  update_request_doc.approved_by = user
  update_request_doc.approved_on = now_datetime()
  update_request_doc.save()
  return update_request_doc.as_dict()


@frappe.whitelist()
def reject(update_request: str) -> dict:
  """
  Reject an update request.
  :param update_request: The update request's name that will be rejected
  :return:
  """
  user = frappe.session.user

  update_request_doc: UpdateRequest = frappe.get_doc(dt, update_request)
  update_request_doc.status = 'Rejected'
  update_request_doc.rejected_by = user
  update_request_doc.rejected_on = now_datetime()
  update_request_doc.save()
  return update_request_doc.as_dict()


@frappe.whitelist()
def revert(update_request: str) -> dict:
  """
  Revert an update request.
  Given the Update Request is Successful and that it's the latest for the Doctype/Docname combination
  :param update_request: The name of the update request
  :return:
  """
  update_request_doc: UpdateRequest = frappe.get_doc(dt, update_request)
  return update_request_doc.revert()
