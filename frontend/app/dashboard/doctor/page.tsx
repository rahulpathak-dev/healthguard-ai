import { RoleGate } from "@/components/role-gate";
export default function DoctorPage() { return <RoleGate allowed={["doctor", "admin"]}><section className="account-shell"><h1>Clinical workspace</h1><p>Doctor tools require a verified professional role assigned by an administrator.</p></section></RoleGate>; }
