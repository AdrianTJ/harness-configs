/**
 * profile-badge — shows the active pi-profile name in the footer status bar.
 * Installed per profile via settings.json "extensions"; reads the env var the
 * pi-profile wrapper sets, so it stays quiet when pi runs without a profile.
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
	const dir = process.env.PI_CODING_AGENT_DIR;
	if (!dir) return;
	const name = dir.replace(/\/+$/, "").split("/").pop();
	if (!name) return;

	pi.on("session_start", (_event, ctx) => {
		ctx.ui.setStatus("profile", `[${name}]`);
	});
}
