class FSMError(Exception):
  """
  Generic error thrown when an FSMDocument related issue is raised
  """

  def __init__(self, message='Something went wrong with the FSMDocument'):
    super().__init__(message)


class InvalidPartyError(FSMError):
  """
  Error thrown when the wrong party applies an update request
  """

  def __init__(self, wrong_party, correct_party):
    super().__init__(
        message="Invalid Party, must be {correct_party}; got {wrong_party} instead".format(correct_party=correct_party,
                                                                                           wrong_party=wrong_party))


class InvalidFieldTransitionError(FSMError):
  """
  Error thrown when the transition of a Check or Select fields are not valid.
  For example, order.status from Ordered => Completed
  """

  def __init__(self, field):
    super().__init__(message="Invalid Transition of the field '{}'".format(field))


class PendingUpdateRequestError(FSMError):
  """
  Error thrown when an update request is created while another update request is Pending or Pending Approval
  """

  def __init__(self):
    super().__init__(message="Can't proceed with the update. Previous update request needs to be processed")


class MethodNotDefinedError(FSMError):
  """
  Error thrown when a method of a field is not defined

  For example, if update is on status field, and _status method is not defined
  """

  def __init__(self):
    super().__init__(message="Field's method not defined for the FSMDocument")


class MissingRevertDataError(FSMError):
  """
  Error thrown when the called method or function does not return revert_data
  """

  def __init__(self):
    super().__init__(message="Method does not return revert_data. Make sure the function returns the relevant data")


class MissingOrInvalidDataError(FSMError):
  """
  Error thrown when there's a child row update (Add/Remove/Update) and "data" field is empty or in the wrong format
  """

  def __init__(self):
    super().__init__(message="Data field is either missing or invalid to update the child table")
