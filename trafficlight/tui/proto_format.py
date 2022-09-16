from __future__ import annotations

from typing import TYPE_CHECKING

from google.protobuf import descriptor, text_encoding
from rich.style import Style
from rich.text import Text

if TYPE_CHECKING:
    from trafficlight.proto import AnyMessage, Proto

# most of the code here is taken from google.protobuf.text_format with modifications to support rich Text


REQUEST_HEADER = Style(color="#91e1ed")  # light blue
MESSAGE_NAME = Style(color="#FFCB6B")  # light yellow
SUB_MESSAGE_NAME = Style(color="#F0DF8B")  # bright yellow
METHOD_NAME = Style(color="#EEE79E")  # light yellow
METHOD_VALUE = Style(color="#DBBE5E")  # yellow
BRACKETS = Style(color="#5F9EC7")  # light blue
NUMBER = Style(color="#F78C6C")  # light orange
STRING = Style(color="#C3E88D")  # light green
ENUM = Style(color="#C792EA")  # light purple
BOOLEAN = Style(color="#74D6B0")  # light cyan
OTHERVALUE = Style(color="#D683A8")  # light magenta
TYPE = Style(color="#606363", italic=True)  # dark bluish grey

TYPES = {
    1: "double",
    2: "float",
    3: "int64",
    4: "uint64",
    5: "int32",
    6: "fixed64",
    7: "fixed32",
    8: "bool",
    9: "string",
    10: "group",
    11: "message",
    12: "bytes",
    13: "uint32",
    14: "enum",
    15: "sfixed32",
    16: "sfixed64",
    17: "sint32",
    18: "sint64",
}


def get_method_text(proto: Proto, text: Text | None = None) -> Text:
    if text is None:
        text = Text(no_wrap=True)

    text.append(proto.method_name, style=METHOD_NAME)
    text.append(" | ")
    text.append(str(proto.method_value), style=METHOD_VALUE)
    return text


class MessageFormatter:
    def __init__(self, text: Text | None = None, indent: int = 4):
        if text is None:
            self.out = Text()
        else:
            self.out = text

        self.indent_size = indent - 1
        self.current_indent: int = 1

    def add_indent(self):
        indent_template = "│" + " " * self.indent_size
        self.out.append(indent_template * self.current_indent, style=Style(color="grey15"))

    def print_message(self, message: AnyMessage):
        fields = message.ListFields()
        fields = sorted(fields, key=lambda f: 1 if f[0].cpp_type == descriptor.FieldDescriptor.CPPTYPE_MESSAGE else 0)
        # message fields should come last

        for field, value in fields:
            if self._is_map_entry(field):
                for key in sorted(value):
                    entry_submsg = value.GetEntryClass()(key=key, value=value[key])
                    self.print_field(field, entry_submsg)
            elif field.label == descriptor.FieldDescriptor.LABEL_REPEATED:
                for element in value:
                    self.print_field(field, element)
            else:
                self.print_field(field, value)

    @staticmethod
    def _is_map_entry(field):
        return (
            field.type == descriptor.FieldDescriptor.TYPE_MESSAGE
            and field.message_type.has_options
            and field.message_type.GetOptions().map_entry
        )

    def print_field(self, field, value):
        """Print a single field name/value pair."""
        self._print_field_name(field)
        self.out.append(" ")
        self.print_field_value(field, value)
        self.out.append("\n")

    def _print_field_name(self, field: descriptor.FieldDescriptor):
        """Print field name."""
        self.add_indent()

        if field.is_extension:
            self.out.append("[", style=BRACKETS)
            if (
                field.containing_type.GetOptions().message_set_wire_format
                and field.type == descriptor.FieldDescriptor.TYPE_MESSAGE
                and field.label == descriptor.FieldDescriptor.LABEL_OPTIONAL
            ):
                self.out.append(field.message_type.full_name)
            else:
                self.out.append(field.full_name)
            self.out.append("]", style=BRACKETS)
        elif field.type == descriptor.FieldDescriptor.TYPE_GROUP:
            # For groups, use the capitalized name.
            self.out.append(field.message_type.name)
        elif field.cpp_type == descriptor.FieldDescriptor.CPPTYPE_MESSAGE:
            self.out.append("\n")
            self.add_indent()
            self.out.append(field.message_type.name, style=SUB_MESSAGE_NAME)
            self.out.append(f" {field.name}")
        else:
            type_name = TYPES.get(field.type)
            if type_name is not None:
                self.out.append(f"{type_name} ", style=TYPE)
            self.out.append(field.name)

    def print_field_value(self, field, value):
        """Print a single field value (not including name).

        For repeated fields, the value should be a single element.

        Args:
          field: The descriptor of the field to be printed.
          value: The value of the field.
        """
        if field.cpp_type == descriptor.FieldDescriptor.CPPTYPE_MESSAGE:
            self.print_message_field_value(value)
        elif field.cpp_type == descriptor.FieldDescriptor.CPPTYPE_ENUM:
            enum_value = field.enum_type.values_by_number.get(value, None)
            if enum_value is not None:
                self.out.append(f"{field.enum_type.name}.{enum_value.name}:{value}", style=ENUM)
            else:
                self.out.append(str(value), style=ENUM)
        elif field.cpp_type == descriptor.FieldDescriptor.CPPTYPE_STRING:
            self.out.append('"', style=STRING)
            if field.type == descriptor.FieldDescriptor.TYPE_BYTES:
                # We always need to escape all binary data in TYPE_BYTES fields.
                out_as_utf8 = False
            else:
                out_as_utf8 = True
            self.out.append(text_encoding.CEscape(value, out_as_utf8), style=STRING)
            self.out.append('"', style=STRING)
        elif field.cpp_type == descriptor.FieldDescriptor.CPPTYPE_BOOL:
            if value:
                self.out.append("true", style=BOOLEAN)
            else:
                self.out.append("false", style=BOOLEAN)
        elif field.cpp_type in (descriptor.FieldDescriptor.CPPTYPE_FLOAT, descriptor.FieldDescriptor.CPPTYPE_DOUBLE):
            self.out.append(str(value), style=NUMBER)
        elif field.cpp_type in (
            descriptor.FieldDescriptor.CPPTYPE_INT32,
            descriptor.FieldDescriptor.CPPTYPE_INT64,
            descriptor.FieldDescriptor.CPPTYPE_UINT32,
            descriptor.FieldDescriptor.CPPTYPE_UINT64,
        ):
            self.out.append(str(value), style=NUMBER)
        else:
            self.out.append(str(value), style=OTHERVALUE)

    def print_message_field_value(self, value: AnyMessage):
        if not value.ListFields():
            self.out.append("{}", style=BRACKETS)
        else:
            self.out.append("{\n", style=BRACKETS)
            self.current_indent += 1
            self.print_message(value)
            self.current_indent -= 1
            self.add_indent()
            self.out.append("}", style=BRACKETS)
