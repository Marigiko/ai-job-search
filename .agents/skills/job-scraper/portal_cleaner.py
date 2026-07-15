# .agents/skills/job-scraper/portal_cleaner.py
"""Clear saved portal pre-fills before writing new content."""


def clean(page, platform: str) -> None:
    """Clear all saved fields for the given platform."""
    cleaners = {
        "getonbrd": _clean_getonbrd,
    }
    cleaner = cleaners.get(platform)
    if cleaner:
        cleaner(page)


def _clean_getonbrd(page) -> None:
    """Clear Trix editors and reset resume selection on GetOnBoard."""
    # Clear all Trix editors
    editors = page.query_selector_all("trix-editor")
    for editor in editors:
        editor.evaluate("el => el.editor.loadHTML('')")
        editor.dispatch_event("triage-change")
    # Reset resume dropdown to first real option
    resume = page.query_selector("#job_application_resume_id")
    if resume:
        options = resume.query_selector_all("option")
        for opt in options:
            val = opt.get_attribute("value")
            if val:
                resume.select_option(val)
                break
    # Clear salary
    salary = page.query_selector('input[name="job_application[expected_salary]"]')
    if salary:
        salary.fill("")
    # Clear reason
    reason = page.query_selector('textarea[name="job_application[reason_to_apply]"]')
    if reason:
        reason.fill("")
