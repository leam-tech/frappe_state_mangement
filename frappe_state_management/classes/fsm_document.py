import frappe
from frappe import _
from frappe.model.document import Document
from frappe_state_management.classes.fsm_error import MethodNotDefinedError, MissingRevertDataError
from frappe_state_management.frappe_state_management.doctype.update_request.update_request import UpdateRequest
from six import string_types


class FSMDocument(Document):
  # TODO: Add documentation
  update_request: UpdateRequest

  def revert(self, revert_data: dict):
    raise NotImplementedError

  def apply_update_request(self, update_request: UpdateRequest) -> None:
    self.update_request = update_request

    try:
      if self.update_request.status in ('Approved', 'Pending'):
        method_call = None
        if self.update_request.custom_call:
          if '.' in self.update_request.custom_call:
            method_call = frappe.get_attr(self.update_request.custom_call)
          else:
            method_call = getattr(self, self.update_request.custom_call, None)
        else:
          method_call = getattr(self, "_{}".format(self.update_request.docfield), None)
        if not method_call:
          raise MethodNotDefinedError

        data = None
        if self.update_request.data:
          if isinstance(data, string_types):
            data = frappe.parse_json(self.update_request.data)
        revert_data = method_call(**{'data': data})
        if not revert_data:
          raise MissingRevertDataError
        self.add_revert_data(revert_data)

      elif self.update_request.status == 'Pending Approval':
        frappe.throw(_('Update Request is Pending Approval'))
      else:
        frappe.throw(_('Update Request processed. Create a new one for updates'))
    except Exception as e:
      self.add_error_to_update_request(
          "Exception Name: {name}\nException Message: {message}".format(name=type(e).__name__, message=str(e)))

  def set_as_pending_approval(self, approval_party):
    self.update_request.status = 'Pending Approval'
    self.update_request.approval_party = approval_party
    self.update_request.save(ignore_permissions=True)

  def set_as_success(self):
    self.update_request.status = 'Success'
    self.update_request.save(ignore_permissions=True)

  def set_as_failed(self):
    self.update_request.status = 'Failed'
    self.update_request.save(ignore_permissions=True)

  def on_update(self):
    self.set_as_success()

  def on_update_after_submit(self):
    self.set_as_success()

  def add_error_to_update_request(self, error: str):
    self.update_request.error = error
    self.set_as_failed()

  def add_revert_data(self, revert_data):
    self.update_request.revert_data = revert_data
    self.update_request.save(ignore_permissions=True)
