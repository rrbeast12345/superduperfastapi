from fastapi import FastAPI
from pydantic import BaseModel
import shelve
import pickle
from datetime import datetime, timezone

app = FastAPI()
import time
# users = {'231':["231", "Thandi Mkhize", "1976-01-01", True],'341':["341", "oliver gardi", "2008-05-23", False]}

def timestamp():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def fixtime(t):
    return  datetime.fromtimestamp(t, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

class Item(BaseModel):
    id_number: str
    name: str
    dob: str


class Person:
    def __init__(self, id_number, name, dob):
        self.id_number = id_number
        self.name = name
        self.dob = dob
        self.verified = False
        self.income_bracket = -1
        self.age = -1
        self.citizenship_status = False
        self.consents = []
        self.consent_forms = []
        self.payment = []
        self.payment_forms = []
        self.current_grants = []
        self.identifications = []
        self.grant_ids = []






@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/test")
def tester(item: Item):
    return item
@app.post("/verify_identity")
def verify(item: Item):
    print('123')
    with shelve.open('people/people') as db:
        try:
            user = db[item.id_number]
        except:
            return {'error':'form not in database'}


    if item.name == user.name and item.dob == user.dob:

        if user.verified:
            return {'status':'verified', 'biometrics':"match"}
        else:
            return {'status': 'unverified', 'biometrics': "match"}
    else:
        return {'status': 'hidden', 'biometrics': "non-match"}
@app.post("/register")
def register(item: Item):
    with shelve.open('people/people') as db:
        db[item.id_number] = Person(item.id_number, item.name, item.dob)
        return db[item.id_number]
@app.post("/get_user")
def get(id: str):

    with shelve.open('people/people') as db:
        try:
            return db[id]
        except KeyError:
            return 'user does not exist'
@app.post("/delete user")
def delete(id: str):

    with shelve.open('people/people') as db:
        try:
            del db[id]
            return 'user removed'
        except:
            return 'user did not exist'
@app.post("/verify user")
def verify(id: str):

    with shelve.open('people/people') as db:
        try:
            if db[id].verified:
                return 'this user is already verified'
            item = db[id]
            item.verified = True
            db[id] = item
            return 'user verified'
        except:
            return 'user did not exist'
class eligibility(BaseModel):
    id_number:str
    income_bracket:int
    age:int
    citizenship_status:bool
grants = {'business grant':[3, 18, True, ['id', 'business statement']], 'social security':[5, 65, True, ['id', 'proof of previous employment']], 'universal income':[5, 18, True, ['bank statement']], 'homeless shelter':[1, 8, -1, ['id']]}
@app.post('/check_eligibility')
def check(info:eligibility):
    with shelve.open('people/people') as db:
        try:
            user:Person = db[info.id_number]
        except:
            return "this user does not exist"
        for attr in vars(info):
            setattr(user, attr, getattr(info, attr))
        db[info.id_number] = user
    approved_grants = []

    for item in grants.keys():
        if user.income_bracket <= grants[item][0] and user.age >= grants[item][1] and (user.citizenship_status == grants[item][2] or grants[item][2] == -1):
            approved_grants.append((item, grants[item][3]))
    return approved_grants
@app.post('/update_eligibility')
def check(id:str):
    with shelve.open('people/people') as db:
        try:
            user:Person = db[id]
        except:
            return 'user does not exist'

    approved_grants = []
    if user.income_bracket == -1 or user.age == -1:
        return 'user has not entered proper information'

    for item in grants.keys():
        if user.income_bracket <= grants[item][0] and user.age >= grants[item][1] and (user.citizenship_status == grants[item][2] or grants[item][2] == -1):
            approved_grants.append((item, grants[item][3]))
    return approved_grants
class rec(BaseModel):
    id_number: str
    consent_given: bool
    scope: list

@app.post('/record_consent')
def record(form:rec):
    with shelve.open('people/people') as db:

        ids = pickle.load(open('consents/consents.pkl', 'rb'))+1

        pickle.dump(ids, open('consents/consents.pkl', 'wb'))
        ids = str(ids)

        try:
            user:Person = db[form.id_number]
        except:
            return 'user doesn\'t exist'
        if form.consent_given:

            for item in form.scope:
                user.consents.append(item)


            user.consent_forms.append(ids)

            with shelve.open('consents/consents') as cts:
                form = form.__dict__

                form['timestamp'] = timestamp()
                cts[ids] = form

        db[user.id_number] = user

    return {"form": form, "id": ids}
@app.post('/retrieve_consent_form')
def retrieve(id:str):
    with shelve.open('consents/consents') as cts:
        try:
            return cts[id]
        except:
            return 'does not exist'
class payment(BaseModel):
    id_number: str
    wallet_provider: str
    wallet_number: str
@app.post('/set_payment')
def record_pay(form:payment):
    with shelve.open('people/people') as db:

        ids = pickle.load(open('payments/payments.pkl', 'rb'))+1

        pickle.dump(ids, open('payments/payments.pkl', 'wb'))
        ids = str(ids)

        try:
            user:Person = db[form.id_number]
        except:
            return 'user doesn\'t exist'

        user.payment = [form.wallet_provider, form.wallet_number]


        user.payment_forms.append(ids)

        with shelve.open('payments/payments') as cts:
            form = form.__dict__


            form['timestamp'] = timestamp()
            cts[ids] = form


        db[user.id_number] = user

    return {"form": form, "id": ids}
@app.post('/retrieve_pay_form')
def retrieve_pay(id:str):
    with shelve.open('payments/payments') as cts:
        try:
            return cts[id]
        except:
            return 'does not exist'
@app.post('/apply')
def apply(user_id:str, grant:str):


    with shelve.open('people/people') as db:
        try:
            user: Person = db[user_id]
        except:
            return 'user does not exist'
        if grant in user.current_grants:
            return 'grant already applied'

        db[user.id_number] = user
        approved_grants = {}
        if user.income_bracket == -1 or user.age == -1:

            return 'user has not entered proper information'
        for item in grants.keys():
            if user.income_bracket <= grants[item][0] and user.age >= grants[item][1] and (
                    user.citizenship_status == grants[item][2] or grants[item][2] == -1):
                        approved_grants[item] = grants[item][3]
        try:
            reqs = approved_grants[grant]

            for item in reqs:
                if not item in user.identifications:
                    return 'user has not inputted the proper documents: required documents are ' + ', '.join(reqs)



            with shelve.open('grants/grants') as gdb:
                ids = pickle.load(open('grants/grant.pkl', 'rb')) + 1

                pickle.dump(ids, open('grants/grant.pkl', 'wb'))

                gdb[str(ids)] = {'grant':grant, "timestamp":timestamp(), 'machine_time': time.time()}
            user.current_grants.append(grant)
            user.grant_ids.append(str(ids))
            db[user.id_number] = user
        except:
            return 'user is not approved for this grant'
        return {"grant": grant, "user": user, 'id': ids}

@app.post('/enter_identification')
def enter_identification(user_id:str, identification):
    with shelve.open('people/people') as db:
        try:
            user = db[user_id]
        except:
            return 'user doesn\'t exist'
        user.identifications.append(identification)
        db[user_id] = user
        return 'success'
@app.post('/track_application_status')
def track_application_status(user_id:str, grant:str):

    with shelve.open('people/people') as db:
        user = db[user_id]
        if not grant in user.current_grants:
            return {'application_status': False}

        ids = user.grant_ids[user.current_grants.index(grant)]


        with shelve.open('grants/grants') as gdb:
            gr = gdb[ids]

        t = 0

        while (t+gr['machine_time']) < time.time():
            t += 604800

        return {'application_status': True, 'approved': gr['timestamp'],'next payment':fixtime(gr['machine_time']+t),'application id':ids}










