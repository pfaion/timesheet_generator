# Timesheet generation script for Hiwis.

###
### Use following section to set your personal default values!
###
default_name = 'Faion, Patrick'
default_unit_of_organisation = ""
default_hours = 24
default_days_of_week = [0, 1, 2, 3, 4]
default_start_hour = 8
default_end_hour = 20
default_max_hours = 6
default_output_file_name = 'timesheet'
default_state = 'NI'
###
###
###

# imports
import datetime
import argparse
import holidays
import calendar
import datetime
import numpy as np
import random
import os

###
### PARSE ARGUMENTS
###

# default date is current month
default_month = datetime.date.today().month
default_year = datetime.date.today().year

# parse arguments
parser = argparse.ArgumentParser(description='Generate University Timesheets.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-n', help='name of the employee', default=default_name)
parser.add_argument('-y', help='year', type=int, default=default_year)
parser.add_argument('-m', help='month', type=int, default=default_month)
parser.add_argument('-dow', help='days of the week (monday = 0, tuesday = 1, ...)', type=int, nargs='*', default=default_days_of_week)
parser.add_argument('-uoo', help='unit of organisation', default=default_unit_of_organisation)
parser.add_argument('-hrs', help='hours', type=int, default=default_hours)
parser.add_argument('-s', help='start time', type=int, default=default_start_hour)
parser.add_argument('-e', help='end time', type=int, default=default_end_hour)
parser.add_argument('-o', help='output file name', default=default_output_file_name)
parser.add_argument('-max', help='maximum hours for a day', type=int, default=default_max_hours)
parser.add_argument('-state', help='german state for public holiday considerations, from list: BW, BY, BE, BB, HB, HH, HE, MV, NI, NW, RP, SL, SN, ST, SH, TH', default=default_state)

args = parser.parse_args()

# get parsed arguments
name = args.n
uoo = args.uoo
year = args.y
month = args.m
days_of_week = args.dow
hours = args.hrs
work_start = args.s
max_hours = args.max
work_end = args.e
filename = args.o

###
### HELPER FUNCTIONS
###

def format_timedelta(td):
    '''Format datetime.timedelta as "hh:mm".'''
    s = td.total_seconds()
    return "{:0>2d}:{:0>2d}".format(int(s // 3600), int((s % 3600) // 60))

def weighted_choice(choices):
    '''Select random choice from list of (option, weight) pairs according to the weights.'''
    choices = list(choices)
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w >= r:
            return c, w
        upto += w
    return c, w


###
### DATA GENERATION
###

# get public holidays and legth of the month
public_holidays = holidays.DE(state='NI', years=year)
days_in_month = calendar.monthrange(year, month)[1]

# check which days are valid, i.e. are specified workdays and not holidays
valid_days = []
for day in range(1, days_in_month + 1):
    date = datetime.date(year, month, day)
    if date not in public_holidays and date.weekday() in days_of_week:
        valid_days.append(day)

# distribute hours over valid days. use exponential weights (after random shuffle) for days, so some days are used often and some are used rarely
possible_days = valid_days
random.shuffle(possible_days)
weights = list(1 / np.arange(1, len(possible_days) + 1))

# collector for sampled distribution
# day => (start, end)
collector = dict()

# possible chunks over the day are from start to end in steps of half-hours
chunk_starts = np.arange(work_start, work_end, 0.5)

# distribute all hours
h = hours
while h > 0:
    if len(possible_days) == 0:
        raise RuntimeError("Could not work off all hours with given parameters!")
    # select day
    day, weight = weighted_choice(zip(possible_days, weights))
    # if day is already listed, extend working hours there either before or after
    if day in collector:
        start, end = collector[day]
        possible_extensions = []
        if start > work_start:
            possible_extensions.append('before')
        if end < (work_end - 0.5):
            possible_extensions.append('after')
        extension = random.choice(possible_extensions)
        if extension == 'before':
            start -= 0.5
        if extension == 'after':
            end += 0.5
        collector[day] = (start, end)
        if end - start == max_hours:
            possible_days.remove(day)
            weights.remove(weight)
    # if day not yet listed, select random starting chunk
    else:
        start = random.choice(chunk_starts)
        end = start + 0.5
        collector[day] = (start, end)
    # half and hour was distributed off
    h -= 0.5


###
### FORMATTING DATA
###

# extract relevant data from work distribution
# list entries are strings: (day, start_time, end_time, duration, recording_date)
data = []
for day in range(1, days_in_month + 1):
    if day in collector:
        date = datetime.date(year, month, day)
        s, e = collector[day]
        s_h = int(s)
        s_m = int((s % 1) * 60)
        e_h = int(e)
        e_m = int((e % 1) * 60)
        start = datetime.datetime.combine(date, datetime.time(s_h, s_m))
        end = datetime.datetime.combine(date, datetime.time(e_h, e_m))
        duration = end - start
        data.append((
            "{}.".format(day),
            start.strftime("%H:%M"),
            end.strftime("%H:%M"),
            format_timedelta(duration),
            date.strftime("%d.%m.")
        ))
    else:
        data.append((
            "{}.".format(day),
            "",
            "",
            "",
            ""
        ))

# additional format strings
header_date = "{:0>2d}/{}".format(month, year)
total_hours_formatted = format_timedelta(datetime.timedelta(hours=hours))


###
### LATEX TEMPLATE
###

tex_pieces = [
# begin

r"""
\documentclass[11pt]{scrartcl}
\usepackage[a4paper, top=0cm, left=0cm, right=0cm, bottom=0cm]{geometry}

\usepackage{graphicx}
\usepackage{fontspec}
\setmainfont{Arial}

\usepackage{booktabs}

\usepackage{array}
\makeatletter
\g@addto@macro{\endtabular}{\rowfont{}}% Clear row font
\makeatother
\newcommand{\rowfonttype}{}% Current row font
\newcommand{\rowfont}[1]{% Set current row font
   \gdef\rowfonttype{#1}#1%
}
\newcolumntype{P}{>{\rowfonttype}p}


\setlength\parindent{0pt}

\begin{document}
\thispagestyle{empty}

\includegraphics[width=0.35\paperwidth]{logo.png}

\vspace{1cm}


\begin{addmargin}{2.2cm}
  
  \begin{tabular}{l l}
    \textbf{\large Vorlage zur Erfassung der geleisteten Arbeitszeiten} & \\
  \end{tabular}
  
  \vspace{0.3cm}
  \begin{tabular}{p{.4\linewidth} p{.53\linewidth}}
    \textbf{Name, Vorname} & \\
    \textbf{der Mitarbeitering/des Mitarbeiters:} & """,
    
# Name

r"""
    \\ \cmidrule{2-2}
    ~& \\
    \textbf{Organisationseinheit:} & """,

# Organisationseinheit

r"""
    \\ \cmidrule{2-2}
    ~& \\
    \textbf{Monat/Jahr:} & """,

# Monat/Jahr

r"""
    \\ \cmidrule{2-2}
  \end{tabular}

  \vspace{1cm}

  \begin{tabular}{| P{1.3cm} | P{1.3cm} | P{1.1cm} | P{1.3cm} | P{1.3cm} | P{2cm} | P{5cm} |}
    \hline
    \rowfont{\scriptsize}
    Kalender-tag & Beginn (Uhrzeit) & Pause (Dauer) & Ende (Uhrzeit) & Dauer (Summe) & aufgezeichnet am: & Bemerkungen\\ \hline
    \rowfont{\normalsize}
    &&&&&&\\\hline""",

# data

r"""
  \end{tabular}

  \vspace{1.5cm}

  $\rule{7.9cm}{0.2mm}$ ~~~ $\rule{7.9cm}{0.1mm}$

  \vspace{0.3cm}
  \footnotesize
  Datum \hspace{0.5cm} Unteschrift des Arbeitnehmbers \hspace{2.2cm} Datum \hspace{0.5cm} Unterschrift Leiterin / Leiter der OE

\end{addmargin}

\end{document}
"""
]

entry_template = "{}&{}&&{}&{}&{}&\\\\\\hline\n"


### 
### BUILD LATEX
###

# write template to file and fill it with the data
with open("{}.tex".format(filename), "w") as f:
    f.write(tex_pieces[0])
    f.write(name)
    f.write(tex_pieces[1])
    f.write(uoo)
    f.write(tex_pieces[2])
    f.write(header_date)
    f.write(tex_pieces[3])
    for entries in data:
        f.write(entry_template.format(*entries))
    f.write(entry_template.format(r"\textbf{Summe}", "", "", total_hours_formatted, ""))
    f.write(tex_pieces[4])

# compile latex and remove additional files
os.system("lualatex {}.tex".format(filename))
os.remove("{}.aux".format(filename))
os.remove("{}.log".format(filename))
os.remove("{}.tex".format(filename))



