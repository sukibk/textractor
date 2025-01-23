import re
import pandas as pd

data = ['Nichols, Marc (FAA) <Marc.Nichols@faa.gov>, Deshazo, Mercedes O (FAA) <Mercedes.O.Deshazo@faa.gov>, Rivera, Erin I (FAA) <Erin.I.Rivera@faa.gov>, Peter, Lorelei (FAA) <lorelei.peter@faa.gov>, Vachon, Matthew E (FAA) <matthew.e.vachon@faa.gov>, Cotton, Tracy (FAA) <tracy.cotton@faa.gov>, Runo Richardson <runorichardson@hotmail.com>, Worden, Christopher J (FAA) <Christopher.J.Worden@faa.gov>, cjworden17@gmail.com <cjworden17@gmail.com>, pvercelli@airlines.org <pvercelli@airlines.org>, info@iacwashington.org <info@iacwashington.org>, leslie.abbott@wnco.com <leslie.abbott@wnco.com>, PWeber@blueorigin.com <PWeber@blueorigin.com>, KMahoney@blueorigin.com <KMahoney@blueorigin.com>, jamie_co@yahoo.com <jamie_co@yahoo.com>, maren.matal@wnco.com <maren.matal@wnco.com>, Shereen.govender@wnco.com <Shereen.govender@wnco.com>, Bnolen@archer.com <Bnolen@archer.com>, Andrew Cummins <andrew.cummins@archer.com>, eric.lentell@archer.com <eric.lentell@archer.com>, Lynda.tran@dot.gov <Lynda.tran@dot.gov>, tpdalebox@gmail.com <tpdalebox@gmail.com>, Peter.hyun@dot.gov <Peter.hyun@dot.gov>, iris.lan@nasa.gov <iris.lan@nasa.gov>, tarabmcdaniel@gmail.com <tarabmcdaniel@gmail.com>, Bradmims87@verizon.net <Bradmims87@verizon.net>, smdickson79@gmail.com <smdickson79@gmail.com>, Jeputnam1876@gmail.com <Jeputnam1876@gmail.com>, Andrew.Wright@klgates.com <Andrew.Wright@klgates.com>, agerchick@kaplankirsch.com <agerchick@kaplankirsch.com>, MGerchick@gerchickmurphy.com <MGerchick@gerchickmurphy.com>, rob.shook@gmail.com <rob.shook@gmail.com>, Houston Mills <hmills@ups.com>, gcastanias@jonesday.com <gcastanias@jonesday.com>, mdombroff@foxrothschild.com <mdombroff@foxrothschild.com>, gfharbo@nsa.gov <gfharbo@nsa.gov>, Michael Robbins <MRobbins@auvsi.org>, Lisa Ellman <lisa.ellman@hoganlovells.com>, j.perkins@stantonchase.com <j.perkins@stantonchase.com>, rcgovan1@gmail.com <rcgovan1@gmail.com>, MWarren@jenner.com <MWarren@jenner.com>, Ken.Quinn@clydeco.us <Ken.Quinn@clydeco.us>, NCalio@airlines.org <NCalio@airlines.org>, earl.adams@hoganlovells.com <earl.adams@hoganlovells.com>, Christopher.A.Haney@Rolls-Royce.com <Christopher.A.Haney@Rolls-Royce.com>, arjun.garg@hoganlovells.com <arjun.garg@hoganlovells.com>, roscoe.howard@btlaw.com <roscoe.howard@btlaw.com>, andrew@modelleader.com <andrew@modelleader.com>, JPiza@prpa.pr.gov <JPiza@prpa.pr.gov>, thomas.dunlap@ntsb.gov <thomas.dunlap@ntsb.gov>, casey.blaine@ntsb.gov <casey.blaine@ntsb.gov>, justine.harrison@aopa.org <justine.harrison@aopa.org>, stella.belvisi@airbus.com <stella.belvisi@airbus.com>, jeffrey.page@fedex.com <jeffrey.page@fedex.com>, nyspena@gmail.com <nyspena@gmail.com>, Molly.Wilkinson@aa.com <Molly.Wilkinson@aa.com>, james.conneely@united.com <james.conneely@united.com>, spenceroverton@gmail.com <spenceroverton@gmail.com>, paulette.j.morant@gmail.com <paulette.j.morant@gmail.com>, robert.letteney@delta.com <robert.letteney@delta.com>, jana.lozano@delta.com <jana.lozano@delta.com>, howard.kass@skyryse.com <howard.kass@skyryse.com>, mwbury@hotmail.com <mwbury@hotmail.com>, dreaphil7713@gmail.com <dreaphil7713@gmail.com>, peter.beshar@us.af.mil <peter.beshar@us.af.mil>, akcajun@live.com <akcajun@live.com>']

def extract_info(entry):
    email_pattern = r"<(.+?)>"
    name_pattern = r"(.+?)\s<"

    email_match = re.search(email_pattern, entry)
    name_match = re.search(name_pattern, entry)

    if email_match:
        email = email_match.group(1)
    else:
        email = entry

    if name_match:
        full_name = name_match.group(1)
        names = full_name.split()
        first_name = names[0]
        last_name = names[-1] if len(names) > 1 else ""
    else:
        first_name = ""
        last_name = ""

    return first_name, last_name, email


records = [extract_info(entry) for entry in data]

df = pd.DataFrame(records, columns=["First Name", "Last Name", "E-Mail"])
df.to_excel("mailing_list.xlsx", index=False)
print("Data has been written to mailing_list.xlsx")