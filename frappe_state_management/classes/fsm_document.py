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

  def revert(self, update_request: UpdateRequest):
    self.update_request = update_request
    self.is_revert = True

    for revert_item in update_request.revert_items:
      doc: Document = frappe.get_doc(revert_item.dt, revert_item.docname)
      revert_data = frappe._dict(self.parse_data(revert_item.revert_data))
      if revert_item.change_type == 'Create':
        meta = frappe.get_meta(revert_item.dt)
        # If submittable, cancel the doc instead of delete
        if meta.get('is_submittable', None):
          doc.cancel()
        else:
          doc.delete()
      elif revert_item.change_type == 'Update':
        doc.update(revert_data)
        doc.save()
      elif revert_item.change_type == 'Remove':
        doc = frappe.new_doc(revert_item.dt)
        doc.update(revert_data)
        doc.save()

    if len(update_request.revert_items):
      self.set_as_reverted()

    return self.update_request

  def apply_update_request(self, update_request: UpdateRequest) -> None:
    self.update_request = update_request
    self.doc_before_save = copy.copy(self)
    self.validate_child_table()
    try:
      if self.update_request.status in ('Approved', 'Pending'):
        method_call = None
        revert_data = None
        if self.update_request.custom_call:
          if '.' in self.update_request.custom_call:
            method_call = frappe.get_attr(self.update_request.custom_call)
          else:
            method_call = getattr(self, self.update_request.custom_call, None)
        elif frappe.get_hooks('fsm_fields', {}).get(self.doctype, {}).get(self.update_request.docfield):
          revert_data = frappe.call(frappe.get_hooks('fsm_fields', {}).get(self.doctype, {}).get(self.update_request.docfield)[-1], self)
        else:
          method_call = getattr(self, "_{}".format(self.update_request.docfield), None)
        
        if not (method_call or revert_data):
          raise MethodNotDefinedError

        if not revert_data and method_call:
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
    if self.get('update_request') and not self.is_pending_approval():
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
    if self.self.get('update_request') and not self.is_pending_approval():
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

  def is_child_add(self):
    return self.update_request.type == 'Add Child Row'

  def is_child_update(self):
    return self.update_request.type == 'Update Child Row'

  def is_child_delete(self):
    return self.update_request.type == 'Delete Child Row'

  def parse_data(self, data=None):
    return frappe._dict(frappe.parse_json(frappe.parse_json(copy.copy(data or self.update_request.data))))

  def validate_child_table(self):
    # Validate if `data` field is not provided, raise Error
    if self.update_request.type in child_row_methods:
      if not self.update_request.data:
        raise MissingOrInvalidDataError
      # Check if the data can be parsed to dict
      try:
        data = self.parse_data()
      except:
        raise MissingOrInvalidDataError
      # If we are deleting or updating a child, verify if the child_row exists
      if self.update_request.type in ['Update Child Row', 'Delete Child Row']:
        if not any([x.name == data.get('name', None) for x in getattr(self, self.update_request.docfield, [])]):
          raise MissingOrInvalidDataError
