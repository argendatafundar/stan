from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import Field
    
    AbstractField = Field
    """
    A field that is abstract and will be implemented by the subclass.
    If the subclass doesn't specify the Field, it will raise an error.
    """
else:
    from abc import abstractmethod

    """
    TODO: Using @abstractmethod for the wrapper will produce an "can't instantiate
    abstract class without an implementation for abstract METHOD".
    This is confusing due to the fact that it's a Field rather than a method.

    Maybe we can use a custom metaclass to wrap the Field and raise the error.
    """

    def AbstractField(*args, **kwargs):
        return property(abstractmethod(lambda: ...))