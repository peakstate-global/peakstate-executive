#!/usr/bin/env python3
"""Build the forum demo case pack: a realistic 48-page executive leadership team pack (ticket 84).

    python3 evals/forum-prep/case-demo/build.py          # writes pack.pdf and profile.docx, then runs the check
    python3 evals/forum-prep/case-demo/build.py --check  # check only

Built to the layout of real public board packs: cover, order of business, formalities, minutes, action log,
numbered papers in one paper template, scorecards with RAG status, a ranking table, a 5 by 5 risk heat map,
financials, attachments, a scanned letter (physical page 32, image only, slightly rotated with noise),
a confidential item, a glossary and a close. HTML is printed to PDF by headless Chrome. Printed page = physical page.
Every organisation, person and figure is invented. Addresses use example.org only.
"""
import base64, html, io, os, random, re, subprocess, sys, tempfile
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, "pack.pdf")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
ORG = "Coralline Coast Water"
FORUM = "Executive Leadership Team"
DATE = "Tuesday 15 December 2026"
N_PAGES, SCAN_PAGE = 48, 32
R = random.Random(8414)  # fixed seed: filler tables are the same on every build

E = html.escape


def tbl(head, rows, cls=""):
    h = "".join(f"<th>{E(str(c))}</th>" for c in head)
    body = ""
    for r in rows:
        body += "<tr>" + "".join(cell(c) for c in r) + "</tr>"
    return f'<table class="{cls}"><tr>{h}</tr>{body}</table>'


RAG = {"Green": "g", "Amber": "a", "Red": "r", "On track": "g", "Monitor": "a", "Off track": "r",
       "Low": "g", "Medium": "a", "High": "r", "Extreme": "x"}


def cell(c):
    c = str(c)
    if c in RAG:
        return f'<td class="rag {RAG[c]}">{E(c)}</td>'
    return f"<td>{E(c)}</td>"


def P(*xs):
    return "".join(f"<p>{E(x)}</p>" for x in xs)


def H(x):
    return f"<h3>{E(x)}</h3>"


def UL(*xs):
    return "<ul>" + "".join(f"<li>{E(x)}</li>" for x in xs) + "</ul>"


def header_block(item, title, ptype, sponsor, author, record, late=False):
    flag = '<span class="late">LATE PAPER</span>' if late else ""
    return (f'<div class="ph"><div class="pi">Item {E(item)}</div><h2>{E(title)}</h2>{flag}'
            f'<table class="meta"><tr><td>Paper type</td><td>{E(ptype)}</td></tr>'
            f'<tr><td>Sponsor</td><td>{E(sponsor)}</td></tr><tr><td>Author</td><td>{E(author)}</td></tr>'
            f'<tr><td>Record no.</td><td>{E(record)}</td></tr></table></div>')


def bars(title, series, max_v=100, unit="%"):
    """Simple grouped bar chart (SVG): series = [(label, [q1, q2, q3, q4])]."""
    w, h, left, top = 620, 230, 150, 20
    rows = []
    bh = 7
    y = top
    cols = ["#9db7c9", "#6f97b3", "#3f7398", "#1b4f72"]
    for label, vals in series:
        rows.append(f'<text x="{left - 8}" y="{y + 16}" text-anchor="end" font-size="11">{E(label)}</text>')
        for i, v in enumerate(vals):
            bw = (w - left - 40) * v / max_v
            rows.append(f'<rect x="{left}" y="{y + i * bh}" width="{bw:.1f}" height="{bh - 1}" fill="{cols[i]}"/>')
        rows.append(f'<text x="{left + (w - left - 40) * vals[-1] / max_v + 4:.1f}" y="{y + 4 * bh - 1}" font-size="9">{vals[-1]}{unit}</text>')
        y += 4 * bh + 8
    leg = "".join(f'<rect x="{left + i * 110}" y="{y + 6}" width="10" height="10" fill="{c}"/>'
                  f'<text x="{left + 14 + i * 110}" y="{y + 15}" font-size="10">{q}</text>'
                  for i, (c, q) in enumerate(zip(cols, ["Dec 2025", "Mar 2026", "Jun 2026", "Sep 2026"])))
    return (f'<div class="fig"><div class="figt">{E(title)}</div><svg viewBox="0 0 {w} {y + 24}" width="100%">'
            f'{"".join(rows)}{leg}</svg></div>')


# ---------------------------------------------------------------- people (all invented)
MD = "Catherine Lowrie, Managing Director"
CFO = "Daniel Okafor, Chief Financial Officer"
EGM_ID = "Priya Ramanathan, Executive General Manager Infrastructure Delivery"
EGM_PS = "Graham Ellery, Executive General Manager People and Safety"
EGM_CR = "Sophie Brennan, Executive General Manager Customer and Regulation"
GC = "Rhys Atherton, General Counsel and Company Secretary"
EGM_NO = "Leanne Fairbairn, Executive General Manager Network Operations"

# ---------------------------------------------------------------- pages
PAGES = {}


def page(n, item, body, kind="std"):
    PAGES[n] = (item, body, kind)


page(1, "", f"""<div class="cover"><div class="logo">CCW</div><div class="org">{ORG}</div>
<div class="ct">{FORUM}</div><div class="cs">Meeting pack</div>
<table class="meta cov"><tr><td>Date</td><td>{DATE}</td></tr><tr><td>Time</td><td>9.00 am to 12.30 pm</td></tr>
<tr><td>Venue</td><td>Boardroom, Level 4, 22 Mangrove Street, Port Calloway, and Teams</td></tr>
<tr><td>Meeting no.</td><td>ELT 2026/12</td></tr><tr><td>Secretariat</td><td>Office of the Managing Director, elt.secretariat@example.org</td></tr></table>
<p class="conf">CONFIDENTIAL. This pack is for members of the {FORUM} and invited attendees only.</p></div>""", "cover")

AGENDA = [
    ["1", "Opening, Acknowledgement of Country, apologies", "Chair", "Note", "9.00", "3"],
    ["2", "Declarations of interest", "Chair", "Note", "9.05", "3"],
    ["3.1", "Minutes of the meeting held 17 November 2026", "Chair", "Approve", "9.05", "4"],
    ["3.2", "Action log", "Secretariat", "Note", "9.10", "6"],
    ["4.1", "Managing Director's report", "C. Lowrie", "Note", "9.15", "7"],
    ["5.1", "Quarterly operational performance report, Q1 FY2027", "C. Lowrie", "Note", "9.30", "10"],
    ["5.2", "Enterprise risk report", "R. Atherton", "Endorse", "9.50", "15"],
    ["5.3", "Finance report, November 2026", "D. Okafor", "Note", "10.10", "20"],
    ["", "Morning tea", "", "", "10.30", ""],
    ["6.1", "Northern depot consolidation and fleet electrification, Stage 1", "P. Ramanathan", "Approve", "10.45", "25"],
    ["6.2", "People and safety report", "G. Ellery", "Note", "11.25", "33"],
    ["7.1", "Customer and regulatory update (late paper)", "S. Brennan", "Note", "11.45", "38"],
    ["7.2", "Major projects status report", "P. Ramanathan", "Note", "12.00", "42"],
    ["8.1", "Board meeting debrief, 4 December 2026", "C. Lowrie", "Verbal", "12.10", "-"],
    ["8.2", "Christmas and New Year on-call arrangements", "L. Fairbairn", "Verbal", "12.15", "-"],
]
page(2, "Agenda", f"""<h1>Order of business</h1>
<p>{FORUM}, meeting ELT 2026/12, {DATE}, 9.00 am.</p>
{tbl(["No.", "Item", "Owner", "Action", "Time", "Page"], AGENDA, "agenda")}
<p class="note">Starred items are for discussion. All other items for noting are taken as read unless a member asks for discussion before 5 pm on Monday 14 December. Starred: 5.1, 6.1, 7.1.</p>""")

page(3, "Agenda", f"""<h1>Order of business (continued)</h1>
{tbl(["No.", "Item", "Owner", "Action", "Time", "Page"], [
    ["9.1", "Enterprise agreement negotiations update (confidential)", "G. Ellery", "Note", "12.20", "46"],
    ["10", "Confirm actions and matters for communication", "Chair", "Note", "12.25", "-"],
    ["11", "Meeting evaluation and close", "Chair", "Note", "12.28", "-"]], "agenda")}
<h3>Members</h3>
{UL(MD + " (Chair)", CFO, EGM_ID, EGM_PS, EGM_CR, GC, EGM_NO)}
<p>In attendance: Mei Lin Tan, Manager Strategy and Performance (item 5.1); Josh Kirkland, Program Manager Depots (item 6.1); Secretariat.</p>
<p>Quorum: a majority of members, including the Managing Director or a delegate.</p>
<h3>Apologies</h3><p>None received at the time of issue.</p>
<h3>Standing register of interests</h3>
{tbl(["Member", "Interest", "Action"], [
    ["Daniel Okafor", "Director, Port Calloway Community Credit Union", "Leave the room for any banking item"],
    ["Sophie Brennan", "Member, state Water Industry Customer Council", "Noted"],
    ["Priya Ramanathan", "Spouse employed by a civil contractor on the panel", "Not to assess panel tenders"]])}""")

page(4, "Item 3.1", f"""<h1>Minutes of the {FORUM} meeting held 17 November 2026</h1>
<p>Meeting ELT 2026/11. Boardroom, Port Calloway, 9.00 am to 12.40 pm.</p>
<p>Present: Catherine Lowrie (Chair), Daniel Okafor, Priya Ramanathan, Graham Ellery, Sophie Brennan, Rhys Atherton, Leanne Fairbairn.</p>
<p>Apologies: nil. Declarations: no new interests declared.</p>
<h3>1. Minutes and actions</h3>
<p>The minutes of 20 October 2026 were confirmed as a true and accurate record. The action log was noted.</p>
<h3>2. Managing Director's report</h3>
<p>The Managing Director noted the Board's focus on field safety and on the cost of the capital programme.</p>
<p>The ELT noted the report.</p>
<h3>3. Northern depot consolidation: early concept</h3>
<p>The EGM Infrastructure Delivery presented a concept to merge the Ashby and Kurrajong Flat depots into one Northern depot.</p>
<p>The CFO asked that any depot proposal show whole-of-life costs, including charging and power supply.</p>
<p>The EGM Network Operations asked that crews keep a working depot through any move.</p>
<p>The ELT agreed the concept should return as a full paper after the Gate 2 review.</p>""")

page(5, "Item 3.1", f"""<h1>Minutes, 17 November 2026 (continued)</h1>
<h3>4. Operational scorecard: use of rankings</h3>
<p>The Managing Director proposed a firmer rule for the divisional ranking in the quarterly scorecard.</p>
<p><b>Resolution ELT 2026/41.</b> That the ELT adopts the following rule from the Q1 FY2027 report:</p>
<ul><li>A division ranked last for two quarters in a row brings a recovery plan to the next meeting.</li>
<li>The executive who owns that division explains the result at that meeting.</li>
<li>A division ranked first shares what worked, so other divisions can adopt it.</li></ul>
<p>Moved: C. Lowrie. Carried.</p>
<h3>5. Enterprise risk report</h3>
<p>The General Counsel noted the Ashby depot lease and the confined space compliance items. The ELT endorsed the report.</p>
<h3>6. People and safety</h3>
<p>The EGM People and Safety reported two lost-time injuries in Field services in October.</p>
<p>The ELT asked for training dates for 2027 to come to the December meeting.</p>
<h3>7. Other business</h3>
<p>Nil. The meeting closed at 12.40 pm. Next meeting 15 December 2026.</p>
<p class="sig">Confirmed as a true and accurate record: ______________________ Chair &nbsp;&nbsp; Date: ___________</p>""")

page(6, "Item 3.2", f"""<h1>Action log</h1>
<p>Open and recently closed actions. Owner initials as in the agenda.</p>
{tbl(["Ref", "Action", "Owner", "Due", "Status"], [
    ["A-2026-29", "Report on customer call wait times at the November peak", "S. Brennan", "Nov 2026", "Closed"],
    ["A-2026-33", "Review on-call allowance for Field services crews", "G. Ellery", "Dec 2026", "In progress"],
    ["A-2026-36", "Draft 2027 mandatory training calendar to ELT", "G. Ellery", "Dec 2026", "Closed, see item 6.2"],
    ["A-2026-38", "Depot proposal to pass Gate 2 review by the Investment Review Panel before return to ELT", "P. Ramanathan", "Dec 2026", "In progress"],
    ["A-2026-39", "Whole-of-life cost model for Northern depot", "D. Okafor", "Dec 2026", "In progress"],
    ["A-2026-40", "Field services: brief on missed attendance targets", "L. Fairbairn", "Dec 2026", "Carried from October"],
    ["A-2026-41", "Apply resolution ELT 2026/41 in the Q1 FY2027 scorecard", "M. L. Tan", "Dec 2026", "Closed, see item 5.1"],
    ["A-2026-42", "Water quality audit response to the regulator", "S. Brennan", "Jan 2027", "Not started"]])}
<p class="note">Actions carried for more than two meetings are shown in the Managing Director's report.</p>""")

# ---- 4.1 Managing Director's report: 7 to 9
page(7, "Item 4.1", header_block("4.1", "Managing Director's report", "For noting", MD, "Office of the Managing Director", "D26/48811") + H("Purpose") +
     P("To brief the ELT on matters across the business since the November meeting.") + H("Recommendation") +
     P("That the ELT notes the Managing Director's report.") + H("Summary") +
     UL("Drinking water compliance stayed above 99.9 per cent for the quarter.",
        "Lost-time injuries in Field services rose, and safety is now a standing Board item.",
        "The capital programme is 4 per cent behind its spend profile for the year to date.",
        "The Board asked for a firm plan for the northern depots before its February meeting."))

page(8, "Item 4.1", "<h1>Corporate scorecard, November 2026</h1>" + tbl(
    ["Measure", "Target", "Nov 2026", "Status"], [
        ["Drinking water samples compliant", "99.9%", "99.98%", "Green"],
        ["Unplanned water interruptions per 1,000", "12.0", "10.4", "Green"],
        ["Sewage overflows to the environment", "4", "6", "Red"],
        ["Field jobs attended within target time", "90%", "84%", "Amber"],
        ["Customer satisfaction (index)", "75", "76", "Green"],
        ["Lost-time injury frequency rate", "2.0", "3.4", "Red"],
        ["Operating result, year to date", "$5.1M", "$7.5M", "Green"],
        ["Capital spend against profile", "100%", "96%", "Amber"]]) +
    P("Status bands: Green on or better than target; Amber within 10 per cent of target; Red worse than that.") +
    bars("Field jobs attended within target time, by quarter (%)", [("Field services", [91, 90, 88, 84]), ("Corporate", [93, 92, 91, 90])]))

page(9, "Item 4.1", "<h1>Managing Director's report (continued)</h1>" + H("Key matters") +
     P("The Board met on 4 December. It approved the half-year statement of corporate intent and asked for monthly safety reporting.",
       "I support the Northern depot consolidation in principle, because two old depots cost us more each year.",
       "My condition is that crews never lose a working base during the move.",
       "The water quality audit by the state regulator found no non-compliance. A short report on the audit follows at item 7.1.") +
     H("Actions carried more than two meetings") + UL("A-2026-33 on-call allowance review (People and Safety).") +
     H("Engagement") + P("I visited the Bellcourt and Ridgeview treatment plants and the Ashby depot in November."))

# ---- 5.1 Quarterly operational performance: 10 to 14
page(10, "Item 5.1", header_block("5.1", "Quarterly operational performance report, Q1 FY2027", "For noting", MD,
                                  "Mei Lin Tan, Manager Strategy and Performance", "D26/49102") + H("Purpose") +
     P("To report operational performance for the quarter to 30 September 2026, with the first divisional ranking under resolution ELT 2026/41.") +
     H("Recommendation") + P("That the ELT notes the report and the divisional ranking.") + H("Background") +
     P("The scorecard has 14 measures. Six operating divisions are ranked on a combined index of safety, maintenance and service results.",
       "This is the second quarter the ranking has been shared with the ELT.") +
     H("Consultation") + P("Divisional managers checked their own data. Field services data was confirmed on 2 December."))

page(11, "Item 5.1", "<h1>Scorecard measures, quarter to 30 September 2026</h1>" + tbl(
    ["Measure", "Previous quarter", "This quarter", "Target", "Status"], [
        ["Drinking water samples compliant", "99.96%", "99.98%", "99.9%", "Green"],
        ["Treatment plant availability", "98.1%", "98.7%", "97.5%", "Green"],
        ["Sewer main breaks and chokes per 100 km", "14.2", "15.9", "16.0", "Green"],
        ["Sewage overflows to the environment", "3", "6", "4", "Red"],
        ["Field jobs attended within target time", "88%", "84%", "90%", "Amber"],
        ["Planned maintenance completed on time", "82%", "79%", "85%", "Amber"],
        ["Fleet availability", "94%", "93%", "92%", "Green"],
        ["Lost-time injury frequency rate", "2.6", "3.4", "2.0", "Red"],
        ["Customer complaints per 1,000 connections", "3.1", "2.9", "3.5", "Green"]]) +
    P("Status is set by the band rules in Appendix A of the scorecard manual.",
      "Field jobs attended within target time stays Amber but fell 4 points."))

page(12, "Item 5.1", "<h1>Divisional ranking, quarter to 30 September 2026</h1>" +
     P("Combined index out of 100: safety 40 per cent, planned maintenance 30 per cent, service targets 30 per cent.") + tbl(
    ["Division", "Executive", "Safety", "Maintenance", "Service", "Index", "Rank"], [
        ["Water treatment", "L. Fairbairn", "96", "91", "94", "93.8", "1 of 6"],
        ["Laboratory services", "S. Brennan", "94", "88", "90", "91.0", "2 of 6"],
        ["Capital works", "P. Ramanathan", "88", "86", "85", "86.5", "3 of 6"],
        ["Customer operations", "S. Brennan", "92", "74", "86", "84.8", "4 of 6"],
        ["Wastewater networks", "L. Fairbairn", "81", "77", "80", "79.5", "5 of 6"],
        ["Field services", "L. Fairbairn", "62", "71", "73", "68.0", "6 of 6"]]) +
    P("Rank 1 is the best result. Field services was also ranked 6 of 6 in the quarter to 30 June 2026.",
      "Water treatment moved from rank 2 to rank 1.") +
    bars("Divisional index by quarter", [("Water treatment", [90, 91, 91, 94]), ("Wastewater networks", [80, 81, 79, 80]),
                                          ("Field services", [74, 72, 69, 68])]))

page(13, "Item 5.1", "<h1>Commentary</h1>" + H("Field services") +
     P("Two lost-time injuries and a rise in jobs reached late drove the result.",
       "Vacancies in the northern crews and travel time from Ashby are the main causes named by the division.",
       "No recovery plan was received by the closing date for this pack.") + H("Water treatment") +
     P("All four plants met every compliance sample. Operator-led filter checks cut unplanned outages by a third.",
       "The division moved to rank 1 for the first time.") + H("Wastewater networks") +
     P("Six overflows followed two storm events in September. Three were at the Kingfisher Creek pump station.") +
     H("Data notes") + P("Safety data closes on the 10th of the following month. Ties share a rank."))

page(14, "Item 5.1", "<h1>Attachment 1: measure detail by month</h1>" + tbl(
    ["Measure", "Jul", "Aug", "Sep", "Quarter"], [
        ["Field jobs attended within target time", "86%", "85%", "82%", "84%"],
        ["Planned maintenance on time", "80%", "79%", "78%", "79%"],
        ["Sewer chokes", "41", "38", "52", "131"],
        ["Water main breaks", "22", "19", "24", "65"],
        ["Odour complaints", "9", "7", "14", "30"],
        ["Fleet availability", "94%", "93%", "92%", "93%"],
        ["Overtime hours, Field services", "1,920", "2,110", "2,380", "6,410"],
        ["Overtime hours, Wastewater networks", "1,050", "990", "1,210", "3,250"]]) +
    tbl(["Plant", "Samples", "Compliant", "Outages"], [
        ["Bellcourt WTP", "1,204", "1,204", "1"], ["Ridgeview WTP", "988", "988", "0"],
        ["Kesterton WTP", "640", "640", "2"], ["Mullet Bay WTP", "412", "411", "0"]]))

# ---- 5.2 Enterprise risk report: 15 to 19
page(15, "Item 5.2", header_block("5.2", "Enterprise risk report", "For endorsement", GC, "Risk and Compliance Team", "D26/49230") +
     H("Purpose") + P("To present the strategic risk register and proposed residual ratings for endorsement.") +
     H("Recommendation") + P("That the ELT endorses the strategic risk register and the proposed residual ratings for referral to the Audit and Risk Committee.") +
     H("Summary") + UL("Two risks are rated High after treatment: SR-02 workforce safety and SR-05 ageing assets.",
                       "SR-09 depot transition is a new risk this quarter.",
                       "One compliance obligation falls due in the first half of 2027 and needs a plan (page 19)."))


def heatmap():
    lik = ["Almost certain", "Likely", "Possible", "Unlikely", "Rare"]
    con = ["Insignificant", "Minor", "Moderate", "Major", "Severe"]
    score = lambda l, c: (5 - l) * (c + 1)
    band = lambda s: "x" if s >= 15 else "r" if s >= 10 else "a" if s >= 5 else "g"
    place = {(1, 3): "SR-02", (2, 3): "SR-05, SR-09", (2, 2): "SR-01", (3, 3): "SR-04", (2, 1): "SR-06",
             (3, 2): "SR-03", (1, 2): "SR-08", (4, 4): "SR-07"}
    rows = ""
    for l in range(5):
        rows += f"<tr><th>{lik[l]}</th>" + "".join(
            f'<td class="hm {band(score(l, c))}">{place.get((l, c), "")}</td>' for c in range(5)) + "</tr>"
    head = "<tr><th></th>" + "".join(f"<th>{c}</th>" for c in con) + "</tr>"
    return f'<table class="heat">{head}{rows}</table>'


page(16, "Item 5.2", "<h1>Residual risk heat map, December 2026</h1>" +
     P("Likelihood (rows) by consequence (columns). Ratings are after current controls.") + heatmap() +
     '<p class="legend"><span class="rag g">Low</span> <span class="rag a">Medium</span> <span class="rag r">High</span> <span class="rag x">Extreme</span></p>' +
     P("Rating = likelihood score x consequence score. Low 1 to 4, Medium 5 to 9, High 10 to 14, Extreme 15 to 25."))

page(17, "Item 5.2", "<h1>Strategic risk register</h1>" + tbl(
    ["Ref", "Risk", "Owner", "Current residual", "Proposed residual", "Trend"], [
        ["SR-01", "Drinking water quality incident", "EGM Network Operations", "Medium", "Medium", "Steady"],
        ["SR-02", "Serious injury to a field worker", "EGM People and Safety", "High", "High", "Rising"],
        ["SR-03", "Cyber attack on operational technology", "Chief Financial Officer", "Medium", "Medium", "Steady"],
        ["SR-04", "Capital programme cost overrun", "EGM Infrastructure Delivery", "Medium", "Medium", "Steady"],
        ["SR-05", "Failure of ageing treatment and pump assets", "EGM Network Operations", "High", "High", "Rising"],
        ["SR-06", "Sewage overflow causes environmental harm", "EGM Network Operations", "Medium", "Medium", "Rising"],
        ["SR-07", "Loss of key customer data", "EGM Customer and Regulation", "Low", "Low", "Falling"],
        ["SR-08", "Prolonged drought reduces supply", "EGM Network Operations", "Medium", "Medium", "Steady"],
        ["SR-09", "Depot transition disrupts field response", "EGM Infrastructure Delivery", "-", "Medium", "New"]]) +
    P("Controls for each risk are listed in the full register, held by Risk and Compliance."))

page(18, "Item 5.2", "<h1>Changes and emerging risks</h1>" + H("SR-09 depot transition (new)") +
     P("The Ashby depot lease ends on 30 June 2027.",
       "The landlord has confirmed the Ashby lease cannot be extended past 30 June 2027.",
       "Field services crews must have a working base from 1 July 2027.",
       "The proposed residual rating of Medium assumes the new Northern depot opens on time.") +
     H("SR-05 ageing assets") +
     P("The asset condition review found more pump stations at condition 4 than planned. Details are in the major projects report.") +
     H("Rationale for change") +
     P("SR-02 stays High after two lost-time injuries. SR-07 falls to Low after the data clean-up.") +
     H("General Counsel's view") +
     P("I do not support a depot plan that relies on a lease extension, because none is available."))

page(19, "Item 5.2", "<h1>Compliance obligations calendar, January to June 2027</h1>" + tbl(
    ["Obligation", "Area", "Due", "Status"], [
        ["Drinking water quality annual report", "Water treatment", "31 Jan 2027", "On track"],
        ["Environmental licence annual return", "Wastewater networks", "28 Feb 2027", "On track"],
        ["Heavy vehicle registration renewals", "Fleet and depots", "31 Mar 2027", "On track"],
        ["Confined space entry certificates renewed", "Wastewater networks", "30 Apr 2027", "Monitor"],
        ["Dam safety inspection, Bellcourt", "Water treatment", "31 May 2027", "On track"],
        ["Trade waste agreements review", "Customer operations", "30 Jun 2027", "On track"]]) +
    P("Confined space entry certificates for 112 wastewater staff expire on 30 April 2027.",
      "A worker without a current certificate may not enter a confined space.",
      "Status Monitor: a plan is needed to finish renewals before the due date."))

# ---- 5.3 Finance report: 20 to 24
page(20, "Item 5.3", header_block("5.3", "Finance report, November 2026", "For noting", CFO, "Financial Planning and Analysis", "D26/49377") +
     H("Purpose") + P("To report the financial result for the five months to 30 November 2026.") +
     H("Recommendation") + P("That the ELT notes the finance report.") + H("Summary") +
     UL("The operating result is $7.5M, $2.4M (47.1%) favourable to budget year to date.",
        "Revenue is $1.1M favourable from higher water use in a dry spring.",
        "Field services overtime is $0.6M unfavourable year to date.",
        "Capital spend is $41.2M, $1.7M (4.0%) behind profile."))

page(21, "Item 5.3", "<h1>Operating statement, year to date</h1>" + tbl(
    ["$ million", "Actual YTD", "Budget YTD", "Variance", "Full-year budget"], [
        ["Water charges", "62.4", "61.5", "0.9", "148.0"], ["Sewerage charges", "48.9", "48.7", "0.2", "116.9"],
        ["Developer charges", "6.1", "6.2", "(0.1)", "14.8"], ["Other revenue", "3.0", "2.9", "0.1", "7.0"],
        ["Total revenue", "120.4", "119.3", "1.1", "286.7"],
        ["Employee costs", "(38.2)", "(37.9)", "(0.3)", "(91.0)"], ["Overtime, Field services", "(2.1)", "(1.5)", "(0.6)", "(3.6)"],
        ["Materials and contractors", "(29.6)", "(31.4)", "1.8", "(75.4)"], ["Energy", "(8.8)", "(9.1)", "0.3", "(21.9)"],
        ["Depreciation", "(26.4)", "(26.4)", "0.0", "(63.4)"], ["Other expenses", "(7.8)", "(7.9)", "0.1", "(18.9)"],
        ["Operating result", "7.5", "5.1", "2.4", "12.5"]]) +
    P("Figures in brackets are costs or unfavourable variances."))

page(22, "Item 5.3", "<h1>Capital expenditure by programme</h1>" + tbl(
    ["Programme", "Actual YTD", "Budget YTD", "Variance", "Full year"], [
        ["Water treatment renewals", "8.4", "8.9", "(0.5)", "22.0"], ["Water mains renewals", "11.2", "10.8", "0.4", "26.5"],
        ["Sewer pump stations", "7.9", "8.6", "(0.7)", "21.0"], ["Sewer mains relining", "6.3", "6.5", "(0.2)", "15.2"],
        ["Fleet replacement", "1.8", "2.1", "(0.3)", "5.4"], ["Depots and facilities", "0.9", "1.2", "(0.3)", "3.1"],
        ["Digital and technology", "4.7", "4.8", "(0.1)", "11.6"], ["Total", "41.2", "42.9", "(1.7)", "104.8"]]) +
    P("$ million. The depots and facilities budget for FY2027 does not include the Northern depot.",
      "Stage 1 of the Northern depot would need a budget change approved by the Board."))

page(23, "Item 5.3", "<h1>Funding and the CFO's view</h1>" + H("Cash and debt") +
     P("Cash at 30 November was $38.6M. Borrowings are $612M against a limit of $680M set by the Treasurer.") +
     H("Northern depot") +
     P("Finance has not yet received the Gate 2 business case or the whole-of-life cost model (action A-2026-39).",
       "Finance supports Stage 1 only after the Investment Review Panel has endorsed the business case.",
       "The $14.8M would be funded by moving $9.0M from sewer pump station renewals and new borrowing of $5.8M.") +
     H("Outlook") + P("The full-year forecast operating result is $13.9M, $1.4M better than budget."))

page(24, "Item 5.3", "<h1>Attachment 1: operating cost by division, year to date</h1>" + tbl(
    ["Division", "Actual", "Budget", "Variance", "FTE"], [
        ["Water treatment", "9.6", "9.9", "0.3", "88"], ["Wastewater networks", "11.8", "11.6", "(0.2)", "131"],
        ["Field services", "12.9", "12.0", "(0.9)", "96"], ["Fleet and depots", "4.2", "4.1", "(0.1)", "22"],
        ["Laboratory services", "2.3", "2.4", "0.1", "24"], ["Customer operations", "7.7", "7.9", "0.2", "112"],
        ["Capital works", "3.4", "3.6", "0.2", "41"], ["Corporate services", "14.1", "14.6", "0.5", "136"]]) +
    P("$ million except FTE (full-time equivalent staff). Field services includes $2.1M of overtime."))

# ---- 6.1 Northern depot (decision): 25 to 32
page(25, "Item 6.1", header_block("6.1", "Northern depot consolidation and fleet electrification, Stage 1", "For decision",
                                  EGM_ID, "Josh Kirkland, Program Manager Depots", "D26/49518") +
     H("Purpose") + P("To seek approval of Stage 1 of the Northern depot programme.") + H("Recommendation") +
     P("That the ELT:") + UL(
        "approves Stage 1 capital of $14.8 million to build the Northern depot at 14 Kiln Road, Bellgrove;",
        "approves 38 electric light vehicles to replace diesel vehicles at Ashby and Kurrajong Flat; and",
        "endorses the business case for the Board meeting of 18 February 2027.") +
     H("Summary") + P("The Northern depot replaces two old depots with one site closer to growth areas in the north.",
                      "Field services and Wastewater networks crews would move in July 2027."))

page(26, "Item 6.1", "<h1>Background</h1>" +
     P("Ashby depot (leased) and Kurrajong Flat depot (owned) house 74 field staff and 51 vehicles.",
       "Both sites are more than 40 years old. Kurrajong Flat floods in a one-in-ten-year storm.",
       "The ELT discussed an early concept on 17 November 2026 and asked for a full paper.",
       "The Bellgrove site was bought in 2024 and is zoned for a works depot.") + H("Timeline") + tbl(
    ["Milestone", "Date"], [["Board approval", "18 February 2027"], ["Construction start", "March 2027"],
                            ["Practical completion", "June 2027"], ["Crews move in", "July 2027"],
                            ["Ashby depot handed back", "30 June 2027"], ["Kurrajong Flat sold", "December 2027"]]) +
    P("The programme assumes the electricity supply upgrade at Bellgrove is ready by May 2027."))

page(27, "Item 6.1", "<h1>Options</h1>" + tbl(
    ["Option", "Capital", "Ten-year cost", "Comment"], [
        ["A. New Northern depot with electric fleet (recommended)", "$14.8M", "$31.2M", "One site, lower running cost"],
        ["B. New Northern depot with diesel fleet", "$11.6M", "$33.9M", "No power upgrade needed"],
        ["C. Refurbish Kurrajong Flat, relocate Ashby crews to it", "$6.9M", "$35.4M", "Flood risk stays"],
        ["D. Do nothing, seek a new lease near Ashby", "$1.2M", "$38.0M", "No suitable lease found"]]) +
    P("Option A has the lowest ten-year cost. It depends on charging for 38 vehicles from opening day.",
      "Option B can open without the power upgrade but costs $2.7M more over ten years.",
      "Infrastructure Delivery recommends option A."))

page(28, "Item 6.1", "<h1>Strategic alignment and financial implications</h1>" + H("Strategic alignment") +
     P("Supports Strategy 2030 goals 2 (reliable services) and 4 (net zero operations by 2035).") +
     H("Financial implications") +
     P("Stage 1 capital is $14.8M. It is not in the FY2027 capital budget.",
       "Charging infrastructure needs a 1.5 MVA supply upgrade by Tarrin Energy Networks.",
       "The paper assumes the supply upgrade costs $0.9M and is included in the $14.8M.",
       "Operating savings of $1.6M a year start in FY2028.") +
     H("Policy and legislation") + P("Capital Investment Framework (Attachment 2). Land Use Planning Act."))

page(29, "Item 6.1", "<h1>Risks</h1>" + tbl(
    ["Identified risk", "Untreated", "Treatment", "Treated"], [
        ["Construction delay past June 2027", "High", "Early works contract, weekly reporting", "Medium"],
        ["Power upgrade late", "High", "Early application to the distributor", "Medium"],
        ["Crew travel times rise for southern jobs", "Medium", "Keep a satellite yard at Ashby until 2028", "Low"],
        ["Cost overrun", "Medium", "10 per cent contingency", "Low"]]) +
    H("Consultation") + UL("Network Operations: crew rosters and travel times.",
                           "Finance: capital estimate.", "Fleet and depots: vehicle choice.",
                           "Unions: briefing planned for February 2027.") +
    H("Views of the sponsor") + P("I recommend option A. It is the only option that meets our net zero target and closes both old sites."))

page(30, "Item 6.1", "<h1>Attachment 1: staging and crew moves</h1>" + tbl(
    ["Team", "Staff", "From", "Move date"], [
        ["Field services north crews", "38", "Ashby", "1 July 2027"], ["Field services east crews", "12", "Kurrajong Flat", "8 July 2027"],
        ["Wastewater networks maintenance", "18", "Kurrajong Flat", "15 July 2027"],
        ["Fleet workshop", "6", "Ashby", "1 July 2027"]]) +
    P("The satellite yard at Ashby in the risk table would need a new lease. None has been sought.") +
    tbl(["Vehicle class", "Diesel today", "Electric Stage 1", "Charger"], [
        ["Utility (ute)", "31", "24", "22 kW AC"], ["Van", "12", "10", "22 kW AC"],
        ["Light truck", "8", "4", "50 kW DC"]]))

page(31, "Item 6.1", "<h1>Attachment 2: Capital Investment Framework (extract)</h1>" +
     P("Approved by the Board, version 4.2, March 2026. Section 5: approval gates.") + tbl(
    ["Gate", "Purpose", "Who endorses", "When"], [
        ["Gate 0", "Strategic need", "Sponsor executive", "Before concept"],
        ["Gate 1", "Options assessment", "Investment Review Panel", "Before detailed design"],
        ["Gate 2", "Business case", "Investment Review Panel", "Before ELT approval"],
        ["Gate 3", "Contract award", "Delegated officer", "Before contract"]]) +
    P("5.3 A project over $10 million must pass Gate 2 before the ELT approves it.",
      "5.4 The Investment Review Panel report is attached to the ELT paper.",
      "5.5 A project not in the approved capital budget needs a Board budget change."))

# page 32: scanned letter (image only), built below
SCAN_HTML = f"""<html><body style="margin:0;background:#fff;font:15.5pt/1.55 Georgia,serif;color:#111">
<div style="padding:90px 110px">
<div style="display:flex;justify-content:space-between;align-items:center;border-bottom:3px solid #222;padding-bottom:14px">
<div style="font:bold 26pt Helvetica,Arial;letter-spacing:1px">TARRIN<br><span style="font-size:13pt;font-weight:normal">ENERGY NETWORKS</span></div>
<div style="font:10.5pt Helvetica,Arial;text-align:right">Network Connections<br>PO Box 412, Calloway Heads<br>connections@tarrin-energy.example.org</div></div>
<p style="margin-top:36px">2 December 2026</p>
<p>Mr Josh Kirkland<br>Program Manager Depots<br>{ORG}<br>22 Mangrove Street, Port Calloway</p>
<p>Our ref: NC-26-08817</p>
<p><b>Re: Connection application, 14 Kiln Road, Bellgrove (1.5 MVA)</b></p>
<p>Thank you for your application of 9 October 2026.</p>
<p>The supply needs a new feeder from the Bellgrove zone substation.</p>
<p>The feeder is in our works programme for the 2027-28 year.</p>
<p>The site cannot be energised at 1.5 MVA before March 2028.</p>
<p>A temporary supply of up to 200 kVA can be offered from July 2027.</p>
<p>The estimated cost to you is $2.3 million, not including GST.</p>
<p>Please contact our connections team to accept the offer.</p>
<p style="margin-top:34px">Yours sincerely</p><p style="font:italic 20pt 'Brush Script MT',cursive;margin:4px 0">A. Pellegrino</p>
<p>A. Pellegrino<br>Manager, Major Connections</p>
<p style="margin-top:40px;font:10pt Helvetica,Arial;color:#444">Item 6.1, Attachment 3. Received by Infrastructure Delivery 7 December 2026.</p>
</div></body></html>"""

# ---- 6.2 People and safety: 33 to 37
page(33, "Item 6.2", header_block("6.2", "People and safety report", "For noting", EGM_PS, "People and Safety", "D26/49602") +
     H("Purpose") + P("To report safety, workforce and training results, and to present the 2027 mandatory training calendar (action A-2026-36).") +
     H("Recommendation") + P("That the ELT notes the report and the 2027 training calendar.") + H("Summary") +
     UL("Lost-time injury frequency rate is 3.4 against a target of 2.0.",
        "Both lost-time injuries this quarter were in Field services (manual handling).",
        "The 2027 training calendar moves several courses later to fit the training budget."))

page(34, "Item 6.2", "<h1>Safety by division, quarter to 30 September 2026</h1>" + tbl(
    ["Division", "Lost-time injuries", "Medical treatment", "Near misses", "Hazard reports"], [
        ["Water treatment", "0", "1", "14", "61"], ["Wastewater networks", "0", "3", "22", "48"],
        ["Field services", "2", "5", "9", "17"], ["Fleet and depots", "0", "1", "4", "12"],
        ["Capital works", "0", "2", "18", "40"], ["Laboratory services", "0", "0", "3", "9"],
        ["Customer operations", "0", "0", "1", "6"]]) +
    P("Field services reports few near misses for its size, which suggests under-reporting."))

page(35, "Item 6.2", "<h1>Mandatory training calendar 2027</h1>" + tbl(
    ["Course", "Staff", "Planned", "Previous plan"], [
        ["Fire warden", "140", "February 2027", "February 2027"], ["Manual handling", "410", "March 2027", "February 2027"],
        ["Chlorine safety", "88", "April 2027", "April 2027"], ["Traffic control", "96", "May 2027", "March 2027"],
        ["Confined space entry refresher", "112", "July 2027", "March 2027"], ["Working at heights", "160", "August 2027", "August 2027"],
        ["First aid", "380", "September 2027", "September 2027"]]) +
    P("Moving courses later saves $0.3M in FY2027. Training providers confirmed the new dates.",
      "Network Operations was not consulted on the new dates."))

page(36, "Item 6.2", "<h1>Workforce</h1>" + tbl(
    ["Division", "Positions", "Filled", "Vacant", "Overtime % of hours"], [
        ["Water treatment", "92", "88", "4", "6%"], ["Wastewater networks", "138", "131", "7", "9%"],
        ["Field services", "110", "96", "14", "18%"], ["Fleet and depots", "24", "22", "2", "5%"]]) +
    P("Field services has 14 vacancies, 10 of them in the northern crews based at Ashby.",
      "Exit interviews name overtime and the condition of the Ashby depot.",
      "Union consultation on the Northern depot crew moves has not started.",
      "The enterprise agreement requires consultation before any change of work location."))

page(37, "Item 6.2", "<h1>Attachment 1: overtime by month, Field services</h1>" + tbl(
    ["Month", "Hours", "Cost", "Callouts"], [[m, f"{R.randint(600, 820):,}", f"${R.randint(380, 520)}k", R.randint(140, 220)]
                                            for m in ["Jun 2026", "Jul 2026", "Aug 2026", "Sep 2026", "Oct 2026", "Nov 2026"]]) +
    tbl(["Crew", "Base", "Staff", "Vacant"], [["North 1", "Ashby", "14", "4"], ["North 2", "Ashby", "13", "3"],
                                             ["North 3", "Ashby", "11", "3"], ["East", "Kurrajong Flat", "12", "1"],
                                             ["Central", "Port Calloway", "24", "2"], ["South", "Mullet Bay", "22", "1"]]))

# ---- 7.1 Customer and regulatory: 38 to 41 (late paper)
page(38, "Item 7.1", header_block("7.1", "Customer and regulatory update", "For noting", EGM_CR, "Customer and Regulation", "D26/49711", late=True) +
     H("Purpose") + P("To update the ELT on customer results, the regulator and a new funding round.") +
     H("Recommendation") + P("That the ELT notes the update and asks Network Operations to decide whether to apply to the State Water Resilience Fund.") +
     H("Summary") + UL("Customer satisfaction is 76, above target.", "The state regulator's water quality audit found no non-compliance.",
                       "A State Water Resilience Fund round opened on 1 December 2026."))

page(39, "Item 7.1", "<h1>Complaints, quarter to 30 September 2026</h1>" + tbl(
    ["Category", "Previous quarter", "This quarter", "Trend"], [
        ["Billing", "212", "188", "Falling"], ["Water pressure and supply", "96", "104", "Rising"],
        ["Sewer odour", "41", "58", "Rising"], ["Field crew conduct", "12", "9", "Falling"],
        ["Late attendance", "38", "61", "Rising"], ["Water quality (taste, colour)", "27", "19", "Falling"]]) +
    P("Late attendance complaints rose 61 per cent. Most came from the northern suburbs served from Ashby.",
      "The Ombudsman referred four complaints, all about late attendance."))

page(40, "Item 7.1", "<h1>State Water Resilience Fund, round 3</h1>" +
     P("The state government opened round 3 on 1 December 2026.",
       "Grants of up to $2.5 million fund treatment plant resilience upgrades.",
       "Eligible work includes backup power, dosing systems and flood protection.",
       "Applications close on 26 February 2027. A co-contribution of 25 per cent is needed.",
       "Coralline Coast Water received $1.1 million in round 2 for Ridgeview WTP.",
       "No application owner has been named for round 3."))

page(41, "Item 7.1", "<h1>Regulator: drinking water quality audit</h1>" +
     P("The state regulator audited our drinking water quality management plan in October 2026.",
       "The audit found no non-compliance and two opportunities for improvement.",
       "The auditor named Water treatment's operator-led filter checks as good practice for other utilities.",
       "The regulator asked us to present the filter checks at the state water quality forum in March 2027.") +
    tbl(["Finding", "Type", "Owner", "Due"], [["Update the incident protocol contact list", "Improvement", "Water treatment", "Feb 2027"],
                                             ["Record sampling chain of custody digitally", "Improvement", "Laboratory services", "Jun 2027"]]))

# ---- 7.2 Major projects: 42 to 45
page(42, "Item 7.2", header_block("7.2", "Major projects status report", "For noting", EGM_ID, "Project Management Office", "D26/49744") +
     H("Purpose") + P("To report the status of capital projects over $2 million.") + H("Recommendation") +
     P("That the ELT notes the report.") + H("Summary") +
     UL("Of 18 projects, 12 are On track, 4 Monitor and 2 Off track.",
        "Kingfisher Creek pump station upgrade is Off track on cost.",
        "The asset condition review (Attachment 1) is complete."))

PROJ = [["Bellcourt WTP filter renewal", "Water treatment", "6.2", "On track"],
        ["Ridgeview WTP backup generator", "Water treatment", "2.4", "On track"],
        ["Kesterton clear water tank", "Water treatment", "3.8", "Monitor"],
        ["Kingfisher Creek pump station upgrade", "Wastewater networks", "9.6", "Off track"],
        ["Northern trunk sewer relining", "Wastewater networks", "7.1", "On track"],
        ["Mullet Bay outfall repair", "Wastewater networks", "2.9", "Monitor"],
        ["Pump station telemetry renewal", "Wastewater networks", "4.4", "On track"],
        ["Port Calloway mains renewal, stage 3", "Capital works", "8.3", "On track"],
        ["Bellgrove reservoir roof", "Capital works", "2.6", "On track"],
        ["Smart meter pilot", "Customer operations", "3.2", "Monitor"],
        ["Billing system upgrade", "Customer operations", "5.7", "Off track"],
        ["Fleet replacement FY2027", "Fleet and depots", "5.4", "On track"],
        ["Laboratory instrument renewal", "Laboratory services", "2.1", "On track"],
        ["Operational technology security", "Corporate services", "3.9", "On track"],
        ["Ridgeview raw water pipeline", "Capital works", "11.4", "On track"],
        ["Coastal mains, Calloway Heads", "Capital works", "4.0", "Monitor"],
        ["Sewer odour control, Kingfisher", "Wastewater networks", "2.2", "On track"],
        ["Records digitisation", "Corporate services", "2.0", "On track"]]
page(43, "Item 7.2", "<h1>Project status (1 of 2)</h1>" + tbl(["Project", "Area", "Budget $M", "Status"], PROJ[:10]))
page(44, "Item 7.2", "<h1>Project status (2 of 2)</h1>" + tbl(["Project", "Area", "Budget $M", "Status"], PROJ[10:]) +
     P("Kingfisher Creek: tender prices came in 22 per cent over estimate. A revised budget returns in February.",
       "Billing system upgrade: vendor delay of four months."))

page(45, "Item 7.2", "<h1>Attachment 1: asset condition review, critical assets</h1>" +
     P("Condition 1 is very good and condition 5 is very poor. Remaining life is the engineer's estimate.") + tbl(
    ["Asset", "Area", "Condition", "Remaining life", "Renewal funded"], [
        ["Bellcourt WTP chlorine dosing system", "Water treatment", "4", "1 year", "FY2029"],
        ["Ridgeview WTP high-lift pumps", "Water treatment", "2", "12 years", "Not needed"],
        ["Kingfisher Creek pump station", "Wastewater networks", "4", "2 years", "FY2027"],
        ["Mullet Bay pump station", "Wastewater networks", "3", "6 years", "FY2030"],
        ["Ashby depot workshop", "Fleet and depots", "4", "2 years", "Not funded"],
        ["Kesterton WTP clarifier", "Water treatment", "3", "8 years", "FY2031"]]) +
    P("Assets at condition 4 with renewal more than a year away are listed for the next capital review."))

page(46, "Item 9.1", "<h1>Item 9.1: Enterprise agreement negotiations update</h1>" +
     P("CONFIDENTIAL. This paper is provided to members separately and is not included in the general pack.",
       "Sponsor: Graham Ellery, Executive General Manager People and Safety.",
       "Members who need the paper may ask the Secretariat."))

page(47, "Glossary", "<h1>Acronyms and terms</h1>" + tbl(["Term", "Meaning"], [
    ["ELT", "Executive Leadership Team"], ["EGM", "Executive General Manager"], ["WTP", "Water treatment plant"],
    ["LTIFR", "Lost-time injury frequency rate, per million hours worked"], ["MVA", "Megavolt-ampere, a measure of electrical supply"],
    ["kVA", "Kilovolt-ampere, one thousandth of an MVA"], ["FTE", "Full-time equivalent staff"],
    ["Gate 2", "Business case review by the Investment Review Panel"], ["RAG", "Red, amber, green status"],
    ["YTD", "Year to date (financial year from 1 July)"], ["Condition 4", "Poor: major work needed within two years"]]))

page(48, "Close", "<h1>Close of meeting</h1>" + H("Item 10: confirm actions and matters for communication") +
     P("The Secretariat reads back new actions. Members agree what is shared with staff.") +
     H("Item 11: meeting evaluation") + P("Members rate the meeting and the quality of papers in the one-minute survey.") +
     H("Next meeting") + P("Tuesday 2 February 2027, 9.00 am, Boardroom, Port Calloway. Papers close Monday 25 January 2027.") +
     f'<p class="note" style="margin-top:60mm">{ORG} and every person in this pack are fictional. Prepared for a demonstration.</p>')


def chrome(args, out):
    """Run headless Chrome; it can hang on teardown after writing its file, so stop it after 90 s."""
    try:
        subprocess.run([CHROME, "--headless", "--disable-gpu"] + args, capture_output=True, timeout=90)
    except subprocess.TimeoutExpired:
        pass
    assert os.path.exists(out) and os.path.getsize(out) > 0, out


def scan_png():
    with tempfile.TemporaryDirectory() as t:
        src, png = os.path.join(t, "l.html"), os.path.join(t, "l.png")
        open(src, "w").write(SCAN_HTML)
        chrome(["--hide-scrollbars", f"--user-data-dir={t}/p", "--window-size=1240,1754", f"--screenshot={png}", src], png)
        img = Image.open(png).convert("L")
    img = img.rotate(-0.9, resample=Image.BICUBIC, expand=False, fillcolor=236)
    px = img.load()
    for _ in range(26000):  # speckle noise
        x, y = R.randrange(img.width), R.randrange(img.height)
        px[x, y] = R.choice([150, 180, 255])
    img = img.filter(ImageFilter.GaussianBlur(0.6)).point(lambda v: int(v * 0.93 + 8))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=62)
    return base64.b64encode(buf.getvalue()).decode()


CSS = """@page{size:A4;margin:0}body{margin:0;font:10.5pt/1.45 Helvetica,Arial,sans-serif;color:#1b1b1b}
.page{box-sizing:border-box;width:210mm;height:297mm;padding:26mm 18mm 22mm;position:relative;page-break-after:always;overflow:hidden}
.page.scan{padding:0}.page.scan img{width:210mm;height:297mm;display:block}
.top{position:absolute;top:9mm;left:18mm;right:18mm;font-size:8pt;color:#1b4f72;border-bottom:1.5px solid #1b4f72;padding-bottom:2mm;display:flex;justify-content:space-between}
.foot{position:absolute;bottom:9mm;left:18mm;right:18mm;font-size:7.5pt;color:#555;border-top:.5px solid #aaa;padding-top:2mm;display:flex;justify-content:space-between}
h1{font-size:15pt;color:#1b4f72;margin:0 0 8pt}h2{font-size:15pt;margin:2pt 0 6pt;color:#1b4f72}h3{font-size:11pt;margin:10pt 0 3pt;color:#1b4f72}
p{margin:0 0 5pt}ul{margin:0 0 6pt;padding-left:16pt}li{margin-bottom:2pt}
table{border-collapse:collapse;width:100%;margin:5pt 0 8pt;font-size:9pt}th{background:#1b4f72;color:#fff;text-align:left;padding:3pt 5pt;font-weight:600}
td{border-bottom:.5px solid #bbb;padding:3pt 5pt;vertical-align:top}table.meta td{border:none;padding:1pt 6pt 1pt 0}table.meta td:first-child{color:#666;width:30mm}
.ph{border:1px solid #1b4f72;padding:6pt 9pt;margin-bottom:8pt;background:#f3f7fa}.pi{font-size:9pt;color:#666}
.late{display:inline-block;background:#b03030;color:#fff;font-size:8pt;padding:1pt 5pt;margin-bottom:4pt}
.rag{font-weight:600}.rag.g{background:#cde9cf}.rag.a{background:#fbe3a6}.rag.r{background:#f2b3ad}.rag.x{background:#c0392b;color:#fff}
span.rag{padding:2pt 8pt}
table.heat td.hm{height:22mm;width:26mm;text-align:center;vertical-align:middle;border:2px solid #fff;font-weight:600;font-size:9pt}
.hm.g{background:#8fcf93}.hm.a{background:#f7d26a}.hm.r{background:#ec8a7d}.hm.x{background:#c0392b;color:#fff}
table.heat th{background:#fff;color:#1b1b1b;font-size:8.5pt}
.note{font-size:8.5pt;color:#555}.fig{margin:8pt 0}.figt{font-size:9pt;font-weight:600;color:#1b4f72;margin-bottom:2pt}
.sig{margin-top:18pt}
.cover{padding-top:30mm}.logo{width:24mm;height:24mm;border-radius:50%;background:#1b4f72;color:#fff;font:bold 15pt Helvetica;display:flex;align-items:center;justify-content:center}
.org{font-size:13pt;color:#1b4f72;margin:6mm 0 24mm;letter-spacing:.5px}.ct{font-size:30pt;font-weight:600;color:#1b4f72}.cs{font-size:18pt;color:#555;margin-bottom:22mm}
table.cov{font-size:11pt}.conf{margin-top:40mm;font-size:9pt;color:#b03030;font-weight:600}"""


def build():
    assert sorted(list(PAGES) + [SCAN_PAGE]) == list(range(1, N_PAGES + 1)), sorted(PAGES)
    out = []
    for n in range(1, N_PAGES + 1):
        if n == SCAN_PAGE:
            out.append(f'<div class="page scan"><img src="data:image/jpeg;base64,{scan_png()}"></div>')
            continue
        item, body, kind = PAGES[n]
        top = "" if kind == "cover" else f'<div class="top"><span>{ORG}</span><span>{FORUM} | {DATE}</span></div>'
        foot = (f'<div class="foot"><span>{E(item)}</span><span>CONFIDENTIAL</span><span>Page {n} of {N_PAGES}</span></div>')
        out.append(f'<div class="page">{top}{body}{foot}</div>')
    doc = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(out)}</body></html>"
    with tempfile.TemporaryDirectory() as t:
        src = os.path.join(t, "pack.html")
        open(src, "w").write(doc)
        if os.path.exists(PDF):
            os.remove(PDF)
        chrome(["--no-pdf-header-footer", f"--user-data-dir={t}/p", f"--print-to-pdf={PDF}", src], PDF)
    subprocess.run(["pandoc", os.path.join(HERE, "profile.md"), "-o", os.path.join(HERE, "profile.docx")], check=True)


def text(n):
    return subprocess.run(["pdftotext", "-layout", "-f", str(n), "-l", str(n), PDF, "-"], check=True,
                          capture_output=True, text=True).stdout


# Facts the demo leans on, each on exactly its physical page (the scanned page is checked by eye: it has no text).
FACTS = {
    "Field services 6 of 6": (12, r"Field services\s+L\. Fairbairn.*6 of 6"),
    "Water treatment 1 of 6": (12, r"Water treatment\s+L\. Fairbairn.*1 of 6"),
    "Rule ELT 2026/41": (5, r"ranked last for two quarters in a row brings a recovery plan"),
    "Decision": (25, r"approves Stage 1 capital of \$14\.8 million"),
    "Lease ends": (18, r"cannot be extended past 30 June 2027"),
    "Power assumed May 2027": (26, r"ready by May 2027"),
    "Gate 2 rule": (31, r"must pass Gate 2 before the ELT approves it"),
    "CFO condition": (23, r"Finance supports Stage 1 only after"),
    "Certificates expire": (19, r"expire on 30 April 2027"),
    "Refresher moved": (35, r"Confined space entry refresher\s+112\s+July 2027"),
    "Grant": (40, r"Grants of up to \$2\.5 million"),
    "Chlorine dosing 1 year": (45, r"chlorine dosing system\s+Water treatment\s+4\s+1 year"),
    "Field jobs 84% Amber": (11, r"Field jobs attended within target time\s+88%\s+84%\s+90%\s+Amber"),
}


def check():
    pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", PDF], capture_output=True, text=True).stdout).group(1))
    assert pages == N_PAGES, pages
    assert len(text(SCAN_PAGE).split()) == 0, "scanned page has a text layer"
    for name, (pg, pat) in FACTS.items():
        hits = [n for n in range(1, N_PAGES + 1) if re.search(pat, text(n))]
        assert hits == [pg], (name, hits)
    alltext = "".join(text(n) for n in range(1, N_PAGES + 1))
    for side in ("invitation.txt", "profile.md"):
        alltext += open(os.path.join(HERE, side)).read()
    # Names only: a capitalised "Sample" or "Example" (water "samples" are real content).
    assert not re.search(r"\b(Sample|Example|SAMPLE|EXAMPLE)\b", alltext), "Sample/Example in a name"
    for m in re.findall(r"[\w.-]+@[\w.-]+", alltext):
        assert m.endswith("example.org"), m
    for n in range(2, N_PAGES + 1):
        if n != SCAN_PAGE:
            assert f"Page {n} of {N_PAGES}" in text(n), n
    print(f"check OK: {pages} pages, page {SCAN_PAGE} image only, {len(FACTS)} facts each on their own page, "
          "no Sample/Example names, reserved domains only")


if __name__ == "__main__":
    if "--check" not in sys.argv:
        build()
    check()
