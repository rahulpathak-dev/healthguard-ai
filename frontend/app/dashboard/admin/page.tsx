import { RoleGate } from "@/components/role-gate";
export default function AdminPage() { return <RoleGate allowed={["admin"]}><section className="account-shell"><h1>Administration</h1><p>Administrative tools are protected by server-side admin dependencies.</p></section></RoleGate>; }
