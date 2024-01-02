# Great thanks to https://desktop-notifier.readthedocs.io/en/latest/_modules/desktop_notifier/winrt.html
# and https://github.com/pywinrt/pywinrt/issues/8

import winsdk._winrt as WinRTObject
from winsdk.windows.foundation import IPropertyValue, PropertyType

def unbox_winrt_object(boxed_value: WinRTObject):
    if boxed_value is None:
        return boxed_value
    
    value = IPropertyValue._from(boxed_value)

    # A bunch of early returns, so we don't need `elif`s here.
    if value.type is PropertyType.EMPTY:
        return None
    if value.type is PropertyType.UINT8:
        return value.get_uint8()
    if value.type is PropertyType.INT16:
        return value.get_int16
    if value.type is PropertyType.UINT16:
        return value.get_uint16()
    if value.type is PropertyType.STRING:
        return value.get_string()
    
    # Else
    raise NotImplementedError(f'Unboxing {value.type} is not yet supported.')
