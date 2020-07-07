import copy

import frappe
from frappe import _
from frappe.model.document import Document
from frappe_state_management.classes.fsm_error import MethodNotDefinedError, MissingRevertDataError, \
  MissingOrInvalidDataError
from frappe_state_management.frappe_state_management.doctype.update_request.update_request import UpdateRequest

child_row_methods = ['Add Child Row', 'Update Child Row', 'Delete Child Row']


class FSMDocument(Document):
  # TODO: Add documentation
  update_request: UpdateRequest
  is_revert = False
  doc_before_save: Document

  def revert(self, revert_data: dict):
    raise NotImplementedError

  def apply_update_request(self, update_request: UpdateRequest) -> None:
    self.update_request = update_request
    self.doc_before_save = copy.copy(self)
    self.validate_child_table()
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

        revert_data = method_call()
        if not self.is_pending_approval():
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
    if not self.is_pending_approval():
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
    if not self.is_pending_approval():
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

  def set_as_reverted(self):
    """
    Marks the Update Request as "Reverted"
    :return:
    """
    self.is_revert = False
    self.update_request.status = 'Reverted'

  def has_update_request(self):
    return getattr(self, 'update_request', None)

  def standard_revert_data(self) -> list:
    return [{'dt': self.doctype, 'docname': self.name, 'change_type': 'Update',
             'revert_data': str(self.doc_before_save.as_dict())}]

  def is_pending(self):
    return self.update_request.status == 'Pending'

  def is_pending_approval(self):
    return self.update_request.status == 'Pending Approval'

  def is_approved(self):
    return self.update_request.status == 'Approved'

  def validate_child_table(self):
    # Validate if `data` field is not provided, raise Error
    if self.update_request.type in child_row_methods and not self.update_request.data:
      raise MissingOrInvalidDataError
    # Check if the data can be parsed to dict
    try:
      data = frappe.parse_json(self.update_request.data)
    except:
      raise MissingOrInvalidDataError
    # If we are deleting or updating a child, verify if the child_row exists
    if self.update_request.type in ['Update Child Row', 'Delete Child Row']:
      if not any([x.name == data.get('name', None) for x in getattr(self, self.update_request.docfield, [])]):
        raise MissingOrInvalidDataError
