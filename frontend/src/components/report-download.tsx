"use client";

import { useState } from "react";

export function ReportDownload({ reportId, label = "Download CSV" }: { reportId: number; label?: string }) {
  const [status, setStatus] = useState("");
  async function download() {
    setStatus("Downloading…");
    const response = await fetch(`/api/backend/reports/${reportId}/csv`);
    if (!response.ok) { setStatus("Download failed."); return; }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `paper-portfolio-report-${reportId}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
    setStatus("Downloaded.");
  }
  return <div className="actionControl"><button className="button secondary" type="button" onClick={download}>{label}</button>{status ? <span className="formMessage">{status}</span> : null}</div>;
}
