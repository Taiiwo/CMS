import requests

class Payment():

    def __init__(self):
        self.login = {}
        self.order = {}
        self.billing = {}
        self.shipping = {}
        self.responses = {}

    def login(self, username, password):
        self.login['password'] = password
        self.login['username'] = username

    def set_order(self, id, description, tax, shipping, po_number, ip_adress):
        self.order['orderid'] = id;
        self.order['orderdescription'] = description
        self.order['shipping'] = '{0:.2f}'.format(float(shipping))
        self.order['ipaddress'] = ip_adress
        self.order['tax'] = '{0:.2f}'.format(float(tax))
        self.order['ponumber'] = po_number
        return self.order

    def set_billing(self, first_name, last_name, company, address1, address2,
                   city, state, zip, country, phone, fax, email, website):
        self.billing['firstname'] = first_name
        self.billing['lastname']  = last_name
        self.billing['company']   = company
        self.billing['address1']  = address1
        self.billing['address2']  = address2
        self.billing['city']      = city
        self.billing['state']     = state
        self.billing['zip']       = zip
        self.billing['country']   = country
        self.billing['phone']     = phone
        self.billing['fax']       = fax
        self.billing['email']     = email
        self.billing['website']   = website
        return self.billing

    def set_shipping(self, first_name, lastname, company, address1, address2,
                    city, state, zipcode, country, email):
        self.shipping['firstname'] = first_name
        self.shipping['lastname']  = lastname
        self.shipping['company']   = company
        self.shipping['address1']  = address1
        self.shipping['address2']  = address2
        self.shipping['city']      = city
        self.shipping['state']     = state
        self.shipping['zip']       = zipcode
        self.shipping['country']   = country
        self.shipping['email']     = email
        return self.shipping

    def do_sale(self,amount, ccnumber, ccexp, cvv=False):
        query = {}
        query.update(self.login)
        # Sales Information
        query.update({
            "ccnumber": ccnumber,
            "ccexp": ccexp,
            "amount": '{0:.2f}'.format(float(amount)),
            "type": "sale"
        })
        if cvv:
            query.update({
                "cvv": cvv
            })
        # Order Information
        query.update(self.order)
        # Billing Information
        query.update(self.billing)
        # Shipping Information
        query.update(self.shipping)
        return self.do_post(query)

    def do_post(self, query):
        base_url = "https://secure.networkmerchants.com/api/transact.php"
        return requests.post(base_url, query)

if __name__ == "__main__":
    # NOTE: your username and password should replace the ones below
    gw = Payment()
    gw.login("demo", "password");

    gw.set_billing("John","Smith","Acme, Inc.","123 Main St","Suite 200",
            "Beverly Hills", "CA","90210","US","555-555-5555","555-555-5556",
            "support@example.com", "www.example.com")
    gw.set_shipping("Mary","Smith","na","124 Shipping Main St","Suite Ship",
            "Beverly Hills","CA","90210","US","support@example.com")
    gw.set_order("1234","Big Order",1,2,"PO1234","65.192.14.10")

    r = gw.do_sale("5.00","4111111111111111","1212",'999')
    print(r)

    if r:
        print("Approved")
    elif (rpdb == 2) :
        print "Declined"
    elif (r == 3) :
        print "Error"
