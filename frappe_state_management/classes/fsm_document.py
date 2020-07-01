import frappe
from frappe import _
from frappe.model.document import Document
from frappe_state_management.classes.fsm_error import MethodNotDefinedError
from frappe_state_management.frappe_state_management.doctype.update_request.update_request import UpdateRequest


class FSMDocument(Document):
  # TODO: Add documentation
  update_request: UpdateRequest

  def revert(self, revert_data: dict):
    raise NotImplementedError

  def apply_update_request(self, update_request: UpdateRequest, data=None) -> None:
    self.update_request = update_request

    if self.update_request.status in ('Approved', 'Pending'):
      method_call = None
      if self.update_request.custom_call:
        if '.' in self.update_request.custom_call:
          method_call = frappe.get_attr(self.update_request.custom_call)
        else:
          method_call = getattr(self, self.update_request.custom_call)
      else:
        method_call = getattr(self, "_{}".format(self.update_request.docfield))
      if not method_call:
        raise MethodNotDefinedError
      method_call(**{'data': self.update_request.data})
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
