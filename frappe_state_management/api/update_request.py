import frappe
from frappe_state_management.frappe_state_management.doctype.update_request.update_request import UpdateRequest


@frappe.whitelist()
def approve_update_request(update_request: str) -> dict:
  """
  Approve an update request.
  :return:
  """
  user = frappe.session.user

  update_request_doc: UpdateRequest = frappe.get_doc('Update Request', update_request)
  update_request_doc.status = 'Approved'
  update_request_doc.approved_by = user
  update_request_doc.save()
  return update_request_doc.as_dict()


@frappe.whitelist()
def reject_update_request(update_request: str) -> dict:
  """
  Reject an update request.
  :return:
  """
  user = frappe.session.user

  update_request_doc: UpdateRequest = frappe.get_doc('Update Request', update_request)
  update_request_doc.status = 'Rejected'
  update_request_doc.rejected_by = user
  update_request_doc.save()
  return update_request_doc.as_dict()
