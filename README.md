# Generate timesheets for your university hiwi contract.

This will generate a random timesheet with valid working hours for your given parameters. It considers weekends and even public holidays. You will need python3 to run it (see requirements.txt for a list of needed libraries) and pdflatex installed and on your path.

Many options can be configured though parameters, e.g. you can specify to work only on Mondays and Wednesdays by passing `-dow 0 2`. For continued usage you might want to adjust the default-values directly in your script at the very top.

This tool is only considered for checking the validity of timesheets and not intended for submission.

Have a look at some [example output](example_output.pdf).

```
usage: python3 timesheet.py [-h] [-n N] [-y Y] [-m M] [-dow [DOW [DOW ...]]]
                    [-uoo UOO] [-hrs HRS] [-s S] [-e E] [-o O] [-max MAX]
                    [-state STATE]

Generate University Timesheets.

optional arguments:
  -h, --help            show this help message and exit
  -n N                  name of the employee (default: Faion, Patrick)
  -y Y                  year (default: 2017)
  -m M                  month (default: 5)
  -dow [DOW [DOW ...]]  days of the week (monday = 0, tuesday = 1, ...)
                        (default: [0, 1, 2, 3, 4])
  -uoo UOO              unit of organisation (default: )
  -hrs HRS              hours (default: 24)
  -s S                  start time (default: 8)
  -e E                  end time (default: 20)
  -o O                  output file name (default: timesheet)
  -max MAX              maximum hours for a day (default: 6)
  -state STATE          german state for public holiday considerations, from
                        list: BW, BY, BE, BB, HB, HH, HE, MV, NI, NW, RP, SL,
                        SN, ST, SH, TH (default: NI)
```