import { useState } from "react";
import { useCreateUserMutation, useUpdateUserMutation } from "@/hooks/react-query/use-query-user";
import type { Role } from "@/interfaces/auth.interface";
import type { UpdateUserBody } from "@/dtos/user.dto";
import type { User } from "@/interfaces/user.interface";
import { formErrors } from "@/lib/common/form-errors";
import { roleOptions, rolesManagedBy } from "@/lib/page-libs/users/roles";

/** New account (username generated when empty); the temporary password is kept to show it once. */
export function useUserCreateForm(myRole: Role) {
  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [role, setRole] = useState<Role>("student");
  const [created, setCreated] = useState<{ username: string; password: string } | null>(null);
  const create = useCreateUserMutation();
  const { fields, message } = formErrors(create.error);
  return {
    fullName,
    setFullName,
    username,
    setUsername,
    role,
    setRole,
    created,
    roles: rolesManagedBy(myRole),
    roleOptions: roleOptions(myRole),
    busy: create.isPending,
    fields,
    message,
    submit: () =>
      create.mutate(
        { full_name: fullName, username: username || null, role },
        { onSuccess: (r) => setCreated({ username: r.user.username, password: r.temp_password }) },
      ),
  };
}

/** Edit name and email; org admins also the role. */
export function useUserEditForm(user: User, myRole: Role, onDone: () => void) {
  const [fullName, setFullName] = useState(user.full_name);
  const [email, setEmail] = useState(user.email ?? "");
  const [role, setRole] = useState<Role>(user.role);
  const update = useUpdateUserMutation();
  const { fields, message } = formErrors(update.error);
  const admin = myRole === "org_admin";
  return {
    fullName,
    setFullName,
    email,
    setEmail,
    role,
    setRole,
    admin,
    roleOptions: roleOptions(myRole),
    busy: update.isPending,
    fields,
    message,
    submit: () => {
      const body: UpdateUserBody = { full_name: fullName, email };
      if (admin) body.role = role;
      update.mutate({ id: user.id, body }, { onSuccess: onDone });
    },
  };
}
