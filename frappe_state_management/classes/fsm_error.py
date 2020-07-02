class FSMError(Exception):
  """
  Generic error thrown when an FSMDocument related issue is raised
  """

  def __init__(self, message='Something went wrong with the FSMDocument'):
    super().__init__(message)


class InvalidActorError(FSMError):
  """
  Error thrown when the wrong actor applies an update request
  """

  def __init__(self, wrong_actor, correct_actor):
    super().__init__(
        message="Invalid Actor, must be {correct_actor}; got {wrong_actor} instead".format(correct_actor=correct_actor,
                                                                                           wrong_actor=wrong_actor))


class InvalidFieldTransitionError(FSMError):
  """
  Error thrown when the transition of a Check or Select fields are not valid.
  For example, order.status from Ordered => Completed
  """

  def __init__(self, transition):
    super().__init__(message="Can't transition to {}".format(transition))


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
