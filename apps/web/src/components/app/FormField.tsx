import { cloneElement, isValidElement, useId } from "react";
import { Field, FieldDescription, FieldError, FieldLabel } from "@/components/ui/field";

type ControlProps = { id: string; "aria-invalid"?: boolean; "aria-describedby"?: string };

/**
 * shadcn Field + FieldLabel + control + FieldDescription/FieldError, with the id wiring done once.
 * The control is either a render prop `(props) => <Input {...props} />` or a single element, which
 * receives `id` / `aria-invalid` / `aria-describedby` unless it sets its own id.
 */
export function FormField({
  label,
  error,
  hint,
  className,
  children,
}: {
  label: string;
  error?: string;
  hint?: string;
  className?: string;
  children: ((props: ControlProps) => React.ReactNode) | React.ReactElement<Partial<ControlProps>>;
}) {
  const auto = useId();
  const msgId = `${auto}-msg`;
  const own = typeof children !== "function" && isValidElement(children) ? children.props.id : undefined;
  const id = own ?? auto;
  const props: ControlProps = { id, "aria-invalid": error ? true : undefined, "aria-describedby": error || hint ? msgId : undefined };
  const control = typeof children === "function" ? children(props) : isValidElement(children) ? cloneElement(children, { ...props, ...children.props, id }) : children;
  return (
    <Field data-invalid={error ? true : undefined} className={className}>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      {control}
      {error ? <FieldError id={msgId}>{error}</FieldError> : hint ? <FieldDescription id={msgId}>{hint}</FieldDescription> : null}
    </Field>
  );
}
