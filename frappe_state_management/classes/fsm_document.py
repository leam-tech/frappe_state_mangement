import frappe
from frappe import _
from frappe.model.document import Document
from frappe_state_management.classes.fsm_error import MethodNotDefinedError, MissingRevertDataError
from frappe_state_management.frappe_state_management.doctype.update_request.update_request import UpdateRequest

from six import string_types


class FSMDocument(Document):
  # TODO: Add documentation
  update_request: UpdateRequest
  is_revert = False

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
        if not revert_data or not len(revert_data):
          raise MissingRevertDataError
        self.add_revert_data(revert_data)

        # Finally save the document if there are no exceptions raised
        self.save(ignore_permissions=True)

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
    """
    Set the Update Request as "Success"
    If the method is implemented in the subclass, to be called in the subclass's method as:
    super().on_update()
    :return:
    """
    if self.is_revert:
      self.set_as_reverted()
    else:
      self.set_as_success()

  def on_update_after_submit(self):
    """
        Set the Update Request as "Success"
        If the method is implemented in the subclass, to be called in the subclass's method as:
        super().on_update_after_submit()
        :return:
        """
    if self.is_revert:
      self.set_as_reverted()
    else:
      self.set_as_success()

  def add_error_to_update_request(self, error: str):
    """
    Add the error object to the Update Request and mark it as "Failed"
    :param error: The error string
    :return:
    """
    self.update_request.error = error
    self.set_as_failed()

  def add_revert_data(self, revert_items: list):
    """
    Add the items affected by the Update Request.
    Three types are:
    - Create
    - Update
    - Remove
    :param revert_items: List of items affected by the Update Request
    :return:
    """
    for item in revert_items:
      self.update_request.append('revert_items', item)
    self.update_request.save(ignore_permissions=True)

  def set_as_reverted(self):
    """
    Marks the Update Request as "Reverted"
    :return:
    """
    self.is_revert = False
    self.update_request.status = 'Reverted'
