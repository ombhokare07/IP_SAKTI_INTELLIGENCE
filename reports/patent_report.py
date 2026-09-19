"""Patent report export using the shared evidence-preserving renderer."""
from reports.renderer import markdown_report, html_report

def build_report(report,format="markdown"):
    return html_report(report) if format=="html" else markdown_report(report)
