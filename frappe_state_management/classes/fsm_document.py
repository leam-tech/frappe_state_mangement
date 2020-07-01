import frappe
from frappe import _
from frappe.model.document import Document
from frappe_state_management.frappe_state_management.doctype.update_request.update_request import UpdateRequest


class FSMDocument(Document):
  # TODO: Add documentation
  update_request: UpdateRequest

  def revert(self, revert_data: dict):
    raise NotImplementedError

  def apply_update_request(self, update_request: UpdateRequest, data=None) -> None:
    self.update_request = update_request

    if self.update_request.status in ('Approved', 'Pending'):
      # TODO: Setup calling the relevant function

      # TODO: Call custom methods
      pass
    elif self.update_request.status == 'Pending Approval':
      frappe.throw(_('Update Request is Pending Approval'))
    else:
      frappe.throw(_('Update Request processed. Create a new one for updates'))

  def set_as_pending_approval(self, approval_party):
    self.update_request.status = 'Pending Approval'
    self.update_request.approval_party = approval_party

  def set_as_approved(self):
    self.update_request.status = 'Approved'

  def set_as_rejected(self):
    self.update_request.status = 'Rejected'
