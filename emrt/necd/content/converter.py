from z3c.form.converter import NumberDataConverter
from z3c.form.interfaces import IWidget

import zope
from zope.component import adapter

from emrt.necd.content import MessageFactory as _

symbols = {
    "decimal": ",",
    "group": "",
    "list": ";",
    "percentSign": "%",
    "nativeZeroDigit": "0",
    "patternDigit": "#",
    "plusSign": "+",
    "minusSign": "-",
    "exponential": "E",
    "perMille": "\xe2\x88\x9e",
    "infinity": "\xef\xbf\xbd",
    "nan": "",
}


class NECDNumberDataConverter(NumberDataConverter):
    def __init__(self, field, widget):
        super(NECDNumberDataConverter, self).__init__(field, widget)
        self.formatter.symbols.update(symbols)


@adapter(zope.schema.interfaces.IInt, IWidget)
class NECDIntegerDataConverter(NECDNumberDataConverter):
    """A data converter for integers."""

    type = int
    errorMessage = _("The entered value is not a valid integer literal.")
