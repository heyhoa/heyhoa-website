# FrontSteps / Caliber API v2 reference (generated)

Source: `docs/api/frontsteps-caliber-v2.swagger.json` — title **Caliber API**, version v2.
Base URL: `https://frontsteps.cloud:443/CAPI2_APISandbox` (sandbox). Production tenants use `https://<tenant>.frontsteps.cloud/CAPI2_<Tenant>`.

Auth: header `apiKey: <key>`. Owner/board-scoped reads also accept HTTP Basic (username:password) which narrows `clientlist` to that user's association.

310 paths, 348 operations, 49 schema definitions.

Regenerate with `python scripts/gen_frontsteps_reference.py`.

## Endpoints by resource

### Accounting  ·  1 ops  ·  used in: P3 fines

| Method | Path | Summary |
|---|---|---|
| `POST` | `/api/v2/postfine` | Post Homeowner Fine |

### Architectural  ·  16 ops  ·  used in: P3 ARC workflow

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/architectural/types` | Get Arc Types |
| `GET` | `/api/v2/architectural/item/{ArchitecturalID}` | Get Architectural Item |
| `GET` | `/api/v2/architectural/item/{ArchitecturalID}/{sessionID}` | Get Architectural Item for Client Contact |
| `GET` | `/api/v2/architectural/itemcc/{ArchitecturalID}/{clientcontactid}` | Get Architectural Item for Client Contact |
| `GET` | `/api/v2/architectural/document/{DocumentID}/{DocumentType}` | Get Architectural Document |
| `GET` | `/api/v2/architectural/{architecturalid}/notes` | Get Architectural Notes |
| `GET` | `/api/v2/architectural/{architecturalid}/notes/{type}` | Get Architectural Notes |
| `GET` | `/api/v2/architectural/{architecturalid}/documents` | Get Architectural Documents |
| `POST` | `/api/v2/architectural/{architecturalid}/documentupload/{stepid}/{filename}/{ext}` | Post New Homeowner Document Upload |
| `POST` | `/api/v2/architectural/{architecturalid}/completeupload/{stepid}` | Post New Homeowner Document Completed Event |
| `POST` | `/api/v2/architectural/{architecturalid}/boardapprove/{stepid}/{clientcontactid}/{approvetype}/{rejecttext}` | Post New Board Approval |
| `POST` | `/api/v2/architectural/boardapprove` | Post New Board Approval |
| `POST` | `/api/v2/architectural/savenew` | Post Arc Item |
| `POST` | `/api/v2/architectural/savenew/{contactid}/{requesttypeid}/{userdefinedtype}` | Post Arc Item |
| `POST` | `/api/v2/architectural/note` | Post Arc Note using HTTP Post Body as request |
| `POST` | `/api/v2/architectural/savenote` | Post Arc Note |

### BillingRecord  ·  1 ops  ·  used in: P3 billing

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/billingrecord/{billingRecordId}/units` | Get Units Assigned To Billing Record |

### CCR  ·  1 ops  ·  used in: P4 governing docs

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/ccr/{ccrId}/kblinks` | Get KnowledgeBase Items Linked To CC&amp;R |

### Client  ·  77 ops  ·  used in: P2 board portal

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/clientlist` | Get All Clients |
| `GET` | `/api/v2/client/{clientId}` | Get Specific Client |
| `GET` | `/api/v2/clientlist/{sinceDate}` | Get New/Changed Clients |
| `GET` | `/api/v2/client/{clientId}/{assignmentType}` | Get Client Assignment |
| `GET` | `/api/v2/client/{clientId}/groups` | Get Client Groups |
| `GET` | `/api/v2/client/{clientId}/groups/{sinceDate}` | Get New/Changed Groups |
| `GET` | `/api/v2/client/{clientId}/units` | Get Client Units |
| `GET` | `/api/v2/client/{clientId}/units/{sinceDate}` | Get New/Changed Client Units |
| `GET` | `/api/v2/client/{clientId}/owners/current` | Get Client Owners (Current) |
| `GET` | `/api/v2/client/{clientId}/owners/all` | Get Client Owners (All) |
| `GET` | `/api/v2/client/{clientId}/owners` | Get Client Owners (All) |
| `GET` | `/api/v2/client/{clientId}/contacts/current` | Get Contacts for Current Unit Accounts for Specified Client |
| `GET` | `/api/v2/client/{clientId}/contacts/all` | Get Contacts for All Unit Accounts for Specified Client |
| `GET` | `/api/v2/client/{clientId}/contacts/all/{sinceDate}` | Get New/Changed Contacts for All Unit Accounts for Specified Client |
| `GET` | `/api/v2/client/{clientId}/commonareas` | Get Client Common Areas |
| `GET` | `/api/v2/client/{clientId}/clientcontacts` | Get Client Contacts |
| `GET` | `/api/v2/client/{clientId}/clientcontacts/{sinceDate}` | Get New/Changed Client Contacts |
| `GET` | `/api/v2/client/{clientId}/clientcontactgroups` | Get Client Contact Groups |
| `GET` | `/api/v2/client/{clientId}/clientcontactgroups/{sinceDate}` | Get New/Changed Client Contact Groups |
| `GET` | `/api/v2/client/{clientId}/clientcontact/{clientContactId}/notes` | Get Client Contact Notes |
| `GET` | `/api/v2/client/{clientId}/clientcontact/{clientContactId}/documents` | Get Client Contact Documents |
| `GET` | `/api/v2/client/{clientId}/vendors` | Get Client Vendors |
| `GET` | `/api/v2/client/{clientId}/notes` | Get Client Notes |
| `GET` | `/api/v2/client/{clientId}/documents` | Get Client Documents |
| `GET` | `/api/v2/client/{clientId}/chartofaccounts` | Get Client Chart of Accounts |
| `GET` | `/api/v2/client/{clientId}/coa` | Get Client Chart of Accounts |
| `GET` | `/api/v2/client/{clientId}/billingrecords/all` | Get Client Billing Records (All) |
| `GET` | `/api/v2/client/{clientId}/billingrecords` | Get Client Billing Records (All) |
| `GET` | `/api/v2/client/{clientId}/billingrecords/current` | Get Client Billing Records (Current) |
| `GET` | `/api/v2/client/{clientId}/insurance` | Get Client Insurance |
| `GET` | `/api/v2/client/{clientId}/invoices` | Get Client Invoices |
| `GET` | `/api/v2/client/{clientId}/invoices/{histType}` | Get Client Invoices |
| `GET` | `/api/v2/client/{clientId}/kb/violations` | Get Client Violation KnowledgeBase |
| `GET` | `/api/v2/client/{clientId}/kb/v` | Get Client Violation KnowledgeBase |
| `GET` | `/api/v2/client/{clientId}/kb/maintenance` | Get Client Maintenance KnowledgeBase |
| `GET` | `/api/v2/client/{clientId}/kb/m` | Get Client Maintenance KnowledgeBase |
| `GET` | `/api/v2/client/{clientId}/costcenters` | Get Client Cost Centers |
| `GET` | `/api/v2/client/{clientId}/ccrs` | Get Client CC&amp;Rs |
| `GET` | `/api/v2/client/{clientId}/factsheet` | Get Client Fact Sheet |
| `GET` | `/api/v2/client/{clientId}/resale` | Get Client Resale Info |
| `GET` | `/api/v2/client/{clientId}/hierarchy/docs` | Get Client Documents Hierarchy |
| `GET` | `/api/v2/client/{clientId}/hierarchy/links` | Get Client Links Hierarchy |
| `GET` | `/api/v2/client/{clientId}/maintenance` | Get Client Maintenance Problems (All) |
| `GET` | `/api/v2/client/{clientId}/maintenance/all` | Get Client Maintenance Problems (All) |
| `GET` | `/api/v2/client/{clientId}/workorders/open` | Get Client Maintenance Problems (Open) |
| `GET` | `/api/v2/client/{clientId}/maintenanceenhance/{all}/{sessionid}/{xcount}/{pagenumber}/{refreshdata}` | Get Client Maintenance Enhanced (Paged Maintenance) |
| `GET` | `/api/v2/client/{clientId}/maintenanceenhance/{all}/{sessionid}/{xcount}/{pagenumber}/{refreshdata}/{orderby}/{orderbydir}` | Get Client Maintenance Enhanced (Paged Maintenance) |
| `GET` | `/api/v2/client/{clientId}/violations` | Get Client Violations (All) |
| `GET` | `/api/v2/client/{clientId}/violations/all` | Get Client Violations (All) |
| `GET` | `/api/v2/client/{clientId}/violations/open` | Get Client Violations (Open) |
| `GET` | `/api/v2/client/{clientId}/violationsenhance/{all}/{sessionid}/{xcount}/{pagenumber}/{refreshdata}` | Get Client Violations Enhanced (Paged violations) |
| `GET` | `/api/v2/client/{clientId}/violationsenhance/{all}/{sessionid}/{xcount}/{pagenumber}/{refreshdata}/{orderby}/{orderbydir}` | Get Client Violations Enhanced (Paged violations) |
| `GET` | `/api/v2/client/{clientId}/transactionaccounts` | Get Client Transaction Accounts |
| `GET` | `/api/v2/client/{clientId}/delinquencies` | Get Client Delinquencies |
| `GET` | `/api/v2/client/{clientIdint}/delinquenciesenhance/{sessionid}/{xcount}/{pagenumber}/{refreshdata}` | Get Client Maintenance Enhanced (Paged Maintenance) |
| `GET` | `/api/v2/client/{clientId}/delinquenciesenhance/{sessionid}/{xcount}/{pagenumber}/{refreshdata}/{orderby}/{orderbydir}` | Get Client Maintenance Enhanced (Paged Maintenance) |
| `GET` | `/api/v2/client/{clientId}/architectural/types` | Get Architectural Types by Client. |
| `GET` | `/api/v2/client/{clientId}/architecturalenhance/{histtype}/{sessionid}/{xcount}/{pagenumber}/{refreshdata}/{orderby}/{orderbydir}` | Get Client Architectural Enhanced (Paged Architectural) |
| `GET` | `/api/v2/client/{clientId}/{clientcontactid}/architecturalitems/{histtype}` | Get Client Architectural By Client Contact |
| `GET` | `/api/v2/client/{clientId}/architecturalitems` | Get Client Architectural |
| `GET` | `/api/v2/client/{clientId}/architecturalitems/{histType}` | Get Client Architectural |
| `GET` | `/api/v2/client/{clientId}/otherpayees` | Get Client Other Payees |
| `GET` | `/api/v2/client/{clientId}/logo` | Get Client Logo |
| `GET` | `/api/v2/client/{clientId}/logoobj` | Get Client Logo |
| `GET` | `/api/v2/client/{clientId}/directory/contact` | Get Contact Directory Listing |
| `GET` | `/api/v2/client/{clientId}/directory/clientcontact` | Get ClientContact Directory Listing |
| `GET` | `/api/v2/client/{clientId}/pbk/all` | Get All Passes/Badges/Keys for Specified Client |
| `GET` | `/api/v2/client/{clientId}/pbk/{sinceDate}` | Get All Passes/Badges/Keys for Specified Client Since Specified Date |
| `GET` | `/api/v2/pendingpayments/{clientId}` | Get Pending Payments for Specified Client |
| `GET` | `/api/v2/client/{clientId}/charges/{sinceDate}` | Get Owner Charges for Specified Client |
| `GET` | `/api/v2/client/{clientId}/1099adj/{taxYear}` | Get Vendor 1099 Adjustments |
| `GET` | `/api/v2/client/{clientId}/appliedpayments/{startDate}/{endDate}` | Get Applied Payments (AR) |
| `GET` | `/api/v2/client/{clientId}/latestappliedpayments/{startDate}/{endDate}` | Get Latest Applied Payments (AR) for Charges |
| `GET` | `/api/v2/client/{clientId}/transactions/{tAcctId}/{sinceDate}` | Get Homeowner Ledger Transactions |
| `GET` | `/api/v2/client/{clientId}/transactionsnobalance/{tAcctId}/{sinceDate}` | Get Homeowner Ledger Transactions without running balance |
| `GET` | `/api/v2/client/{clientId}/postingcodes/all` | Get Posting Codes |
| `GET` | `/api/v2/client/{clientId}/unitresale/all` | Get Client Unit Resale Info |

### ClientContact  ·  40 ops  ·  used in: P2 board users

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/clientcontact` | Get Client Contact |
| `GET` | `/api/v2/clientcontact/{clientContactId}` | Get Client Contact |
| `PUT` | `/api/v2/clientcontact/{clientContactId}` | Update Client Contact Info |
| `PATCH` | `/api/v2/clientcontact/{clientContactId}` | Update Client Contact Info |
| `GET` | `/api/v2/clientcontact/{clientcontactId}/clientcontactdetails` | Get Client Contact Details |
| `OPTIONS` | `/api/v2/clientcontact/{clientcontactId}/clientcontactdetails` | Get Client Contact Details |
| `GET` | `/api/v2/clientcontact/{clientContactId}/photo` | Get Client Contact Photo |
| `POST` | `/api/v2/clientcontact/{clientContactId}/photo` | Post New Client Contact Photo |
| `DELETE` | `/api/v2/clientcontact/{clientContactId}/photo` | Delete Client Contact Photo |
| `GET` | `/api/v2/clientcontact/{clientContactId}/photoobj` | Get Client Contact Photo |
| `GET` | `/api/v2/clientcontact/{clientContactId}/signature` | Get Client Contact Signature |
| `POST` | `/api/v2/clientcontact/{clientContactId}/signature` | Post New Client Contact Signature |
| `DELETE` | `/api/v2/clientcontact/{clientContactId}/signature` | Delete Client Contact Signature |
| `GET` | `/api/v2/clientcontact/{clientContactId}/signatureobj` | Get Client Contact Signature |
| `GET` | `/api/v2/clientcontact/{clientContactId}/notes` | Get Client Contact Notes |
| `GET` | `/api/v2/clientcontact/{clientContactId}/documents` | Get Client Contact Documents |
| `GET` | `/api/v2/clientcontact/invoices` | Get Invoices for Client Contact |
| `GET` | `/api/v2/clientcontact/invoices/{histType}` | Get Invoices for Client Contact |
| `GET` | `/api/v2/clientcontact/{clientContactId}/invoices` | Get Invoices for Client Contact by ClientContactID |
| `GET` | `/api/v2/clientcontact/{clientContactId}/invoices/{histType}` | Get Invoices for Client Contact by ClientContactID |
| `GET` | `/api/v2/clientcontact/invoicesinitialize` | Get Invoices for Client Contact |
| `GET` | `/api/v2/clientcontact/invoicesinitialize/{sessionid}/{xcount}/{histType}/{refreshdata}/{orderby}/{orderbydir}` | Get Invoices for Client Contact |
| `GET` | `/api/v2/clientcontact/invoicesenhance/{sessionid}/{xcount}/{pagenumber}/{histtype}` | Get Invoices by Page for Client Contact, used after GetClientContactInvoicesPageStart in invoked |
| `GET` | `/api/v2/clientcontact/invoicesenhance/{sessionid}/{xcount}/{pagenumber}/{histtype}/{orderby}/{orderbydir}` | Get Invoices by Page for Client Contact, used after GetClientContactInvoicesPageStart in invoked |
| `GET` | `/api/v2/clientcontact/{clientcontactid}/optout` |  |
| `GET` | `/api/v2/clientcontact/multipass` | Get summary details for a Client/Client Contact |
| `GET` | `/api/v2/clientcontact/{clientcontactid}/multipass` | Get summary details for a Client/Client Contact From ClientContact Id |
| `GET` | `/api/v2/clientcontact/{clientcontactid}/notifications` |  |
| `PUT` | `/api/v2/clientcontact/{clientContactId}/phone` | Update Client Contact Phone |
| `POST` | `/api/v2/clientcontact/{clientContactId}/phone` | Post New Client Contact Phone |
| `PATCH` | `/api/v2/clientcontact/{clientContactId}/phone` | Update Client Contact Phone |
| `PUT` | `/api/v2/clientcontact/{clientContactId}/email` | Update Client Contact Email |
| `POST` | `/api/v2/clientcontact/{clientContactId}/email` | Post New Client Contact Email |
| `PATCH` | `/api/v2/clientcontact/{clientContactId}/email` | Update Client Contact Email |
| `POST` | `/api/v2/clientcontact/updatenotification/{linkid}/{viewed}` | Update notification view state |
| `POST` | `/api/v2/clientcontact/updateallnotifications/{clientcontactid}/{viewed}` | Update all user notifications view state |
| `PUT` | `/api/v2/clientcontact/{clientContactId}/password` | Change Password |
| `PUT` | `/api/v2/clientcontact/{clientcontactid}/updateoptout` | Update Opt-Out Options |
| `DELETE` | `/api/v2/clientcontact/{clientContactId}/email/{emailId}` | Delete Client Contact Email Address |
| `DELETE` | `/api/v2/clientcontact/{clientContactId}/phone/{phoneId}` | Delete Client Contact Phone |

### ClientContactGroup  ·  2 ops  ·  used in: P4 committees

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/clientcontactgroup/{contactGroupId}/members/all` | Get Client Contact Group Members (All) |
| `GET` | `/api/v2/clientcontactgroup/{contactGroupId}/members/current` | Get Client Contact Group Members (Current) |

### CommonArea  ·  4 ops  ·  used in: P3 requests

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/commonarea/{caId}/maintenance` | Get Common Area Maintenance Problems (All) |
| `GET` | `/api/v2/commonarea/{caId}/maintenance/all` | Get Common Area Maintenance Problems (All) |
| `GET` | `/api/v2/commonarea/{caId}/maintenance/open` | Get Common Area Maintenance Problems (Open) |
| `POST` | `/api/v2/commonarea/{commonAreaId}/servicerequest` | Post New Common Area Service Request |

### Contact  ·  40 ops  ·  used in: P2 homeowner users

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/contact` | Get Contact |
| `OPTIONS` | `/api/v2/contact` | Get Contact |
| `GET` | `/api/v2/contact/{contactId}` | Get Contact |
| `PUT` | `/api/v2/contact/{contactId}` | Update Contact |
| `OPTIONS` | `/api/v2/contact/{contactId}` | Get Contact |
| `PATCH` | `/api/v2/contact/{contactId}` | Update Contact |
| `GET` | `/api/v2/searchcontacts/all/{firstname}/{lastname}` | Search All Contacts |
| `GET` | `/api/v2/searchcontacts/current/{firstname}/{lastname}` | Search Current Contacts |
| `GET` | `/api/v2/contact/{contactId}/contactdetails` | Get Contact Details |
| `OPTIONS` | `/api/v2/contact/{contactId}/contactdetails` | Get Contact Details |
| `GET` | `/api/v2/contact/multipass` | Get summary details for a Contact |
| `GET` | `/api/v2/contact/{contactId}/photo1` | Get Contact Photo1 |
| `POST` | `/api/v2/contact/{contactId}/photo1` | Post New Contact Photo1 |
| `GET` | `/api/v2/contact/{contactId}/photo2` | Get Contact Photo2 |
| `POST` | `/api/v2/contact/{contactId}/photo2` | Post New Contact Photo2 |
| `GET` | `/api/v2/contact/{contactId}/units` | Get Contact Units |
| `GET` | `/api/v2/contact/{contactId}/optout` |  |
| `GET` | `/api/v2/contact/{contactId}/notifications` |  |
| `POST` | `/api/v2/contact/updatenotification/{linkid}/{viewed}` | Update notification view state |
| `POST` | `/api/v2/contact/updateallnotifications/{contactid}/{viewed}` | Update all user notifications view state |
| `PUT` | `/api/v2/contact/{contactId}/phone` | Update Contact Phone Number |
| `POST` | `/api/v2/contact/{contactId}/phone` | Post New Contact Phone Number |
| `PATCH` | `/api/v2/contact/{contactId}/phone` | Update Contact Phone Number |
| `PUT` | `/api/v2/contact/{contactId}/email` | Update Contact Email Address |
| `POST` | `/api/v2/contact/{contactId}/email` | Post New Contact Email Address |
| `PATCH` | `/api/v2/contact/{contactId}/email` | Update Contact Email Address |
| `PUT` | `/api/v2/contact/{contactId}/familymember` | Update Contact Family Member |
| `POST` | `/api/v2/contact/{contactId}/familymember` | Post New Contact Family Member |
| `PATCH` | `/api/v2/contact/{contactId}/familymember` | Update Contact Family Member |
| `PUT` | `/api/v2/contact/{contactId}/pet` | Update Contact Pet |
| `POST` | `/api/v2/contact/{contactId}/pet` | Post New Contact Pet |
| `PATCH` | `/api/v2/contact/{contactId}/pet` | Update Contact Pet |
| `PUT` | `/api/v2/contact/{contactId}/mailmatrix` | Update Contact Mail Matrix |
| `PATCH` | `/api/v2/contact/{contactId}/mailmatrix` | Update Contact Mail Matrix |
| `PUT` | `/api/v2/contact/{contactId}/password` | Change Password |
| `PUT` | `/api/v2/contact/{contactId}/updateoptout` | Update Opt-Out Options |
| `DELETE` | `/api/v2/contact/{contactId}/email/{emailid}` | Delete Contact Email Address |
| `DELETE` | `/api/v2/contact/{contactId}/phone/{phoneid}` | Delete Contact Phone |
| `DELETE` | `/api/v2/contact/{contactId}/familymember/{familymemberid}` | Delete Contact Family Member |
| `DELETE` | `/api/v2/contact/{contactId}/pet/{petid}` | Delete Contact Pet |

### FamilyMember  ·  2 ops  ·  used in: P4 directory

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/familymember/{familyMemberId}/photo` | Get Family Member Photo |
| `POST` | `/api/v2/familymember/{familyMemberId}/photo` | Post New Family Member Photo |

### Group  ·  13 ops  ·  used in: P3 sub-associations

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/group/{groupId}` | Get Group |
| `GET` | `/api/v2/group/{groupId}/{assignmentType}` | Get Group Assignment |
| `GET` | `/api/v2/group/{groupId}/units` | Get Group Units |
| `GET` | `/api/v2/group/{groupId}/commonareas` | Get Group Common Areas |
| `GET` | `/api/v2/group/{groupId}/plat` | Get Group Plat Map |
| `GET` | `/api/v2/group/{groupId}/maintenance` | Get Group Maintenance Problems (All) |
| `GET` | `/api/v2/group/{groupId}/maintenance/all` | Get Group Maintenance Problems (All) |
| `GET` | `/api/v2/group/{groupId}/maintenance/open` | Get Group Maintenance Problems (Open) |
| `GET` | `/api/v2/group/{groupId}/violations` | Get Group Violations (All) |
| `GET` | `/api/v2/group/{groupId}/violations/all` | Get Group Violations (All) |
| `GET` | `/api/v2/group/{groupId}/violations/open` | Get Group Violations (Open) |
| `GET` | `/api/v2/group/{groupId}/delinquencies` | Get Group Delinquencies |
| `POST` | `/api/v2/group/{groupId}/servicerequest` | Post New Group Service Request |

### Invoice  ·  12 ops  ·  used in: P3 AP approvals

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/invoice/{invoiceId}/details` | Get Invoice Details |
| `GET` | `/api/v2/invoice/{invoiceId}/{clientcontactid}/details` | Get Invoice Details |
| `GET` | `/api/v2/invoice/{invoiceId}/lineitems` | Get Invoice Line Items |
| `GET` | `/api/v2/invoice/{invoiceId}/logentries` | Get Invoice Log  Items |
| `GET` | `/api/v2/invoice/{invoiceId}/payments` | Get Invoice Payments |
| `GET` | `/api/v2/invoice/{invoiceId}/notes` | Get Invoice Notes |
| `GET` | `/api/v2/invoice/{invoiceId}/documents` | Get Invoice Documents |
| `POST` | `/api/v2/invoice` | Post Invoice |
| `POST` | `/api/v2/invoice/embed` | Post Invoice |
| `POST` | `/api/v2/invoice/{invoiceId}/action` | Post Invoice Action |
| `POST` | `/api/v2/invoice/{invoiceId}/{clientContactId}/action` | Post Invoice Action by ClientContactID |
| `POST` | `/api/v2/invoice/{invoiceId}/document` | Post New Invoice Document |

### Login  ·  10 ops  ·  used in: P2 portals auth

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/login` |  |
| `POST` | `/api/v2/requestnewuseraccount` | Request New User Account |
| `POST` | `/api/v2/requestnewuseraccountrestricted` | Request New User Account |
| `POST` | `/api/v2/requestnewuseraccountcomplete` | Request New User Account |
| `GET` | `/api/v2/validateportalsettings` | Validation Confirmation |
| `POST` | `/api/v2/requestnewuseraccount/confirm` | Request New User Account Confirmation |
| `POST` | `/api/v2/resetpassword` | Reset Password |
| `POST` | `/api/v2/resetpassword/confirm` | Reset Password Confirmation |
| `POST` | `/api/v2/recoverusername` | Recover Username |
| `POST` | `/api/v2/updateusername/{newUsername}` | Update Username |

### Maintenance  ·  6 ops  ·  used in: P3 requests

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/maintenance/{problemId}` | Get Maintenance Details |
| `GET` | `/api/v2/maintenance/{problemId}/actions` | Get Maintenance Actions |
| `GET` | `/api/v2/maintenance/{problemId}/notes` | Get Maintenance Notes |
| `GET` | `/api/v2/maintenance/{problemId}/pictures` | Get Maintenance Pictures |
| `GET` | `/api/v2/maintenance/{problemId}/documents` | Get Maintenance Documents |
| `POST` | `/api/v2/maintenance/{problemID}/photos` | Post New Photo |

### MgmtCo  ·  7 ops  ·  used in: P2 branding

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/mgmtco` | Get Management Company |
| `GET` | `/api/v2/mgmtco/{logintype}` | Get Management Company |
| `GET` | `/api/v2/mgmtco/logo` | Get Management Company Logo |
| `GET` | `/api/v2/mgmtco/logoobj` | Get Management Company Logo |
| `GET` | `/api/v2/mgmtco/employees` | Get Management Company Employees (All) |
| `GET` | `/api/v2/mgmtco/employees/all` | Get Management Company Employees (All) |
| `GET` | `/api/v2/mgmtco/employees/current` | Get Management Company Employees (Current) |

### Misc  ·  16 ops  ·  used in: P2 health / payment providers

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/time` | Get Server Time |
| `GET` | `/api/v2/ping` | Test Connectivity |
| `GET` | `/api/v2/paymentproviders` | Get Payment Providers |
| `POST` | `/api/v2/paymentproviders` | Get Payment Providers |
| `GET` | `/api/v2/caliberwebsettings` | Get Caliber Portal Settings |
| `GET` | `/api/v2/picture/{picRecId}` | Download Picture or Image |
| `GET` | `/api/v2/picture/{picRecId}/thumb` | Download Picture or Image Thumbnail |
| `GET` | `/api/v2/pictureobj/{picRecId}` | Download Picture or Image Object |
| `GET` | `/api/v2/pictureobj/{picRecId}/thumb` | Download Picture or Image Object Thumbnail |
| `GET` | `/api/v2/note/{noteId}/documents` | Get Note Documents |
| `GET` | `/api/v2/vendornote/{noteId}/documents` | Get Vendor Note Documents |
| `GET` | `/api/v2/document/{documentId}` | Get "Attached" Document |
| `GET` | `/api/v2/printeddocument/{pDocId}` | Get "Printed" Document |
| `GET` | `/api/v2/accountingterms` | Get Accounting Payment Terms |
| `GET` | `/api/v2/phonetypes` | Get Phone Types |
| `GET` | `/api/v2/pbktypes` | Get Passes/Badges/Keys Types |

### OtherPayee  ·  1 ops  ·  used in: P3 AP

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/otherpayee/{otherPayeeId}/payments` | Get Other Payee Payments |

### Payment  ·  5 ops  ·  used in: P3 AR / payments

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/payment/{paymentId}/checkimage` | Get Payment Check Image |
| `GET` | `/api/v2/payment/{paymentId}/stubimage` | Get Payment Stub Image |
| `POST` | `/api/v2/payment` | Post Payment |
| `POST` | `/api/v2/paymentaccepted` | Post Payment Accepted |
| `POST` | `/api/v2/payment/{paymentId}/void` | Post Void Payment |

### Pet  ·  2 ops  ·  used in: P4 directory

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/pet/{petId}/photo` | Get Pet Photo |
| `POST` | `/api/v2/pet/{petId}/photo` | Post New Pet Photo |

### Unit  ·  22 ops  ·  used in: P2 homeowner portal

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/unitlist` | Get Unit List |
| `GET` | `/api/v2/unit/{unitId}` | Get Unit |
| `GET` | `/api/v2/unitlist/{sinceDate}` | Get Unit List Since Date |
| `GET` | `/api/v2/unit/{unitId}/unitaccounts` | Get Unit Accounts (All) |
| `GET` | `/api/v2/unit/{unitId}/unitaccounts/all` | Get Unit Accounts (All) |
| `GET` | `/api/v2/unit/{unitId}/unitaccounts/current` | Get Unit Accounts (Current) |
| `GET` | `/api/v2/unit/{unitId}/unitaccount/current` | Get Unit Accounts (Current) |
| `GET` | `/api/v2/unit/{unitId}/currentowners` | Get Unit Owners (Current) |
| `GET` | `/api/v2/unit/{unitId}/owners/current` | Get Unit Owners (Current) |
| `GET` | `/api/v2/unit/{unitId}/notes` | Get Unit Notes |
| `GET` | `/api/v2/unit/{unitId}/documents` | Get Unit Documents |
| `GET` | `/api/v2/unit/{unitId}/pictures` | Get Unit Pictures |
| `GET` | `/api/v2/unit/{unitId}/resale` | Get Unit Resale Info |
| `GET` | `/api/v2/unit/{unitId}/maintenance` | Get Unit Maintenance (All) |
| `GET` | `/api/v2/unit/{unitId}/maintenance/all` | Get Unit Maintenance (All) |
| `GET` | `/api/v2/unit/{unitId}/maintenance/open` | Get Unit Maintenance (Open) |
| `GET` | `/api/v2/unit/{unitId}/violations` | Get Unit Violations (All) |
| `GET` | `/api/v2/unit/{unitId}/violations/all` | Get Unit Violations (All) |
| `GET` | `/api/v2/unit/{unitId}/violations/open` | Get Unit Violations (Open) |
| `GET` | `/api/v2/unit/{unitId}/delinquencies` | Get Unit Delinquencies |
| `POST` | `/api/v2/unit/{unitId}/servicerequest` | Post Unit Service Request |
| `POST` | `/api/v2/unit/{unitId}/escrowdocsalert` |  |

### UnitAccount  ·  35 ops  ·  used in: P2 homeowner ledger / autopay

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/unitaccount/{unitAccountId}` | Get Unit Account |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/resale` | Get Unit Account Resale Info |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/notes` | Get Unit Account Notes |
| `GET` | `/api/v2/unitaccount/notecategories` | Get Unit Account Note Categoreis |
| `POST` | `/api/v2/unitaccount/{unitAccountId}/addnote` | Post Unit Account Note |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/documents` | Get Unit Account Documents |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/emergencycontacts` | Get Unit Account Emergency Contacts |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/vehicles` | Get Unit Account Vehicles |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/pbk` | Get Unit Account Passes, Badges &amp; Keys |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/violations` | Get Unit Account Violations (All) |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/violations/all` | Get Unit Account Violations (All) |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/violations/open` | Get Unit Account Violations (Open) |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/architectural` | Get Unit Account Architectural (All) |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/architectural/all` | Get Unit Account Architectural (All) |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/architectural/open` | Get Unit Account Architectural (All) |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/maintenance` | Get Unit Account Maintenance (All) |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/maintenance/all` | Get Unit Account Maintenance (All) |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/maintenance/open` | Get Unit Account Maintenance (Open) |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/transactions/{tAcctId}/{fromDate}` | Get Unit Account Transactions |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/transactions/all/{fromDate}` | Get Unit Account Transactions (All Transaction Accounts) |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/ledger/{tAcctId}/{fromDate}` | Get Unit Account Ledger(s) |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/delinquencies` | Get Unit Account Delinquencies |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/contacts` | Get Unit Account Contacts |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/achoptions` | Get ACH Options |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/ach` | Get ACH Definitions and Plans |
| `PUT` | `/api/v2/unitaccount/{unitAccountId}/ach` | Update ACH Definition (and Payment Plans) |
| `POST` | `/api/v2/unitaccount/{unitAccountId}/ach` | Add New ACH Definition (and Payment Plans) |
| `PATCH` | `/api/v2/unitaccount/{unitAccountId}/ach` | Update ACH Definition (and Payment Plans) |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/statements` | Use this method to retrieve an array of available statements by the 'unitAccountId' parameter. |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/statements/{statementId}` | Use this method to retrieve the Statement doc (PDF) of available statements by the 'unitAccountId' and 'statem |
| `GET` | `/api/v2/unitaccount/{unitAccountId}/openchargessummary/{tAcctId}` | Get Open Charges Summary (Open) |
| `PUT` | `/api/v2/unitaccount/{unitAccountId}/achpaymentplan` | Update ACH Payment Plan |
| `POST` | `/api/v2/unitaccount/{unitAccountId}/achpaymentplan` | Add New ACH Payment Plan |
| `PATCH` | `/api/v2/unitaccount/{unitAccountId}/achpaymentplan` | Update ACH Payment Plan |
| `POST` | `/api/v2/unitaccount/{UnitID}/addnewowner` | Add New Owner Account to a Unit |

### Vendor  ·  18 ops  ·  used in: P3 vendors / 1099

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/vendorlist` | Get Vendor List |
| `GET` | `/api/v2/vendorlist/insurance` | Get Vendor List w/Insurance Info |
| `GET` | `/api/v2/vendor/{vendorId}` | Get Vendor |
| `DELETE` | `/api/v2/vendor/{vendorId}` | Delete Vendor |
| `GET` | `/api/v2/vendor/{vendorId}/contacts` | Get Vendor Contacts |
| `GET` | `/api/v2/vendor/{vendorId}/insurance` | Get Vendor Insurance |
| `GET` | `/api/v2/vendor/{vendorId}/workorders` | Get Vendor Maintenance Problems |
| `GET` | `/api/v2/vendor/{vendorId}/invoices` | Get Vendor Invoices |
| `GET` | `/api/v2/vendor/{vendorId}/notes` | Get Vendor Notes |
| `GET` | `/api/v2/vendor/{vendorId}/payments/{days}` | Get Vendor Payments |
| `GET` | `/api/v2/vendor/{vendorId}/documents` | Get Vendor Documents |
| `GET` | `/api/v2/vendor/{vendorId}/1099adj/{taxYear}` | Get Vendor 1099 Adjustments |
| `PUT` | `/api/v2/vendor` | Update Vendor |
| `POST` | `/api/v2/vendor` | Post New Vendor |
| `PUT` | `/api/v2/vendor/{vendorId}/contact` | Update Vendor Contact |
| `POST` | `/api/v2/vendor/{vendorId}/contact` | Post New Vendor Contact |
| `POST` | `/api/v2/vendor/1099adj` | Post Vendor 1099 Adjustments |
| `DELETE` | `/api/v2/vendorcontact/{vContactId}` | Delete Vendor Contact |

### Violation  ·  17 ops  ·  used in: P4 compliance

| Method | Path | Summary |
|---|---|---|
| `GET` | `/api/v2/violation/{violationId}` | Get Violations |
| `GET` | `/api/v2/violation/{violationId}/actions` | Get Violation Actions |
| `GET` | `/api/v2/violation/{violationId}/notes` | Get Violation Notes |
| `GET` | `/api/v2/violation/{violationId}/pictures` | Get Violation Pictures |
| `GET` | `/api/v2/violation/{violationId}/documents` | Get Violation Documents |
| `GET` | `/api/v2/violation/{violationId}/letters` | Get Violation Documents |
| `GET` | `/api/v2/violation/{violationId}/fines` | Get Violation Fines |
| `GET` | `/api/v2/violation/{violationId}/hearings` | Get Violation Hearings |
| `GET` | `/api/v2/violation/{violationId}/ccr` | Get Violation CCR |
| `GET` | `/api/v2/violations/{clientId}/categories` | Get Client KB Categories |
| `GET` | `/api/v2/violations/{clientId}/category/{categoryId}/types` | Get Client KB Item Types |
| `POST` | `/api/v2/violation/savenote` | Post Violation Note |
| `POST` | `/api/v2/violation/note` | Post Arc Note using HTTP Post Body as request |
| `POST` | `/api/v2/violation/{violationId}/documentupload/{filename}/{ext}/{categoryID}/{noteDate}` | Post New Violation Document Upload |
| `POST` | `/api/v2/violation/{violationId}/documentupload/{filename}/{ext}` | Post New Violation Document Upload |
| `POST` | `/api/v2/violation/{violationId}/Image` | Post Violation Image |
| `POST` | `/api/v2/violation` | Create New Violation |

## Schema definitions

- **ACHDefinition**: ACHDefinitionID, AccountType, UnitAccountID, Name, ContactID, AccountNumber, RoutingNumber, BankName, IsActive, IsDeleted, DateCreated, LastModified, IsAuthorized, AuthorizationDate, AuthorizedByLoginID, AuthorizedByName, ACHPaymentPlans
- **ACHPaymentPlan**: ACHPaymentPlanID, ACHDefinitionID, UnitAccountID, Name, IsManual, ManualAmount, StartDate, AuthorizationDate, AuthorizedByLoginID, AuthorizedByName, EndDate, IsActive, Distribution, PaymentPlanType, IsDeleted, DateCreated, LastModified
- **Address**: AddressID, RefID, RefType, IsDeleted, Name, InCareOf, UnitNumber, Address1, Address2, City, State, ZipCode, Country, OneLine
- **AlternateAddress**: AddressID, ContactID, Address, IsDefault, SameAsUnit, MonthDayStart, MonthDayEnd, IsDeleted, DateCreated, CreatedBy, LastModified, ModifiedBy
- **AppliedPaymentAP**: ID, PaymentID, InvoiceID, InvoiceNumber, InvoiceDate, LineItemID, PaymentGLAccountID, CostCenterID, Amount, GLTransactionID, VendorCredit, Desc, UserID, LineItemDescription, DateCreated
- **ArcBoardApproval**: ApprovalID, ApprovalType, ArcItemID, CContactID, ApprovalUserName, StageID, StepID, ApprovalDate, IsDeleted, RejectionReason
- **ArcDocument**: DocumentType, Extension, MimeType, DocID, DocDate, DocName, Link, NoteId, InternalViewOnly, BoardMembersOK
- **ArchitecturalItem**: ArcStepActions, ArchitecturalID, UnitID, UnitAccountID, Status, PrimaryStatus, StartDate, Owner, Address, ApplicationNumber, RequestType, RequestTypeID, NextActionDate, UserDefinedArcType, Documents, Notes, UserActions, RequiresBoardApproval, RequiredNumberOfApprovers, ActualNumberOfApprovals, AlreadyApprovedByThisUser, AlreadyRejectedByThisUser, CanBeApprovedByThisUser, ApprovalStepID, DocumentStepID
- **ArchitecturalNote**: ArchitecturalID, CreatedByName, CategoryID, InternalViewOnly, BoardMembersOK, Note
- **ClientContactInfo**: ClientContactID, Address1, Address2, UnitNumber, City, State, ZipCode, Country, Sync
- **Contact**: ContactID, Title1, FirstName1, MiddleInitial1, LastName1, Suffix1, Title2, FirstName2, MiddleInitial2, NewNotifications, IsPrimary, IsOwner, IsOccupant, IsPrimaryOccupant, IsRenter, Is3rdParty, LastName2, Suffix2, Entity, DisplayName, SameAsUnit, AllowLogIn, AllowLogIn2, LoginID1, LoginID2, OK2Email, SendLetter, dtStart, dtEnd, DOB1, DOB2, OptOut, DOB1Set, DOB2Set, CompanyName, Renter, RentalStartDate, RentalEndDate, UnitAccountID, UnitID, GroupID, ClientID, IsDeleted, DateCreated, LastModified, MailingAddress, Phones, EmailAddresses, FamilyMembers, Pets, AlternateAddress, MailingMatrices, Links
- **ContactUpdate**: ContactID, DisplayName, DOB1, DOB2, DOB1Set, DOB2Set, InCareOf, UnitNumber, Address1, Address2, City, State, ZipCode, Country, SameAsUnit
- **CreateViolationRequest**: ViolationNumber, ClientId, GroupId, UnitId, UnitAccountId, KBCatId, KBItemId, InspectorId, ViolationDate, ClosedDate, Print, LocX, LocY, Latitude, Longitude, Description, Source, Status, AppealDate, RequiredAction, AutoFines, AutoFinesStartDate, UserId
- **Document**: DocumentID, ItemID, ItemType, DocTitle, Extension, AddedBy, UploadDate, DocType, DocPath, UniqueName, DisplayOnWeb, WebCategoryID, IsDeleted, DateCreated, LastModified, Bin, Links, MimeType
- **EmailAddress**: EmailID, RefType, RefID, NameOption, Email, EmailType, EmailTypeName, IsPrimary, IsSecondary, UseInMailMatrix, IsDeleted, DateCreated, CreatedBy, LastModified, ModifiedBy
- **EscrowDocsAlert**: BuyerName, BuyerMailingAddress, EstimatedClosingDate, UnitID, UnitAccountID
- **FamilyMember**: FamilyMemberID, ContactID, Name, DOB, Age, Notes, IsDeleted, DateCreated, LastModified, DOBSet, Links
- **GetPaymentProviderObject**: ContactID, NameOption, AccountNumber, TAcctID, Balance, RedirectUrl, CssUrl
- **Insurance**: InsuranceID, Name, RefType, RefID, InsuranceCompany, PolicyNumber, BeginDate, ExpirationDate, Amount, Deductible, HoldPaymentsOnExpiration, InsuranceTypeID, InsuranceType, Notes, AgentName, AgentCompanyName, Address1, Address2, City, State, ZipCode, Country, Phone, Fax, Cell, Email, MgmtCoAdditionalInsured, Resale, IsDeleted, DateCreated, LastModified
- **Invoice**: InvoiceID, ClientID, InvoiceNumber, APBasis, ActualNumberOfApprovals, Amount, PONumber, AcctTermID, AcctTerm, PaymentTypeID, ManualCheckNumber, ManualPaymentDate, CombinePayments, PaymentGLAccountID, VendorNotes, InvoiceDate, DueDate, Received, ReceivedDate, Validated, ValidatedDate, OnHold, OnHoldDate, APApproved, APApprovedDate, MgrApproved, MgrApprovedDate, BoardApproved, BoardApprovedDate, ReadyToPay, ReadyToPayDate, Rejected, RejectedDate, RejectedBy, RejectedByName, RejectedReason, APPosted, PostingDate, Voided, VoidDate, VoidGLTransactionID, ChangeInvoiceID, Refund, Recurring, UsePrevAmounts, RecInvCategoryID, SchFrequency, SchStartDate, SchEndDate, RecurringDescription, PaymentCCID, InvoiceStatus, AmountPaid, RemainingBalance, RequiredNumberOfApprovers, IsDeleted, DateCreated, LastModified, APAccountID, PayeeID, PayeeType, PayeeName, Note, OnlinePaymentDate, LineItems, Links
- **InvoiceAction**: InvoiceID, ClientContactID, Action, RejectText
- **InvoiceLineItem**: LineItemID, InvoiceID, VendorCode, CostCenterID, ExpenseGLAccountID, Amount, Description, Quantity, UnitOfMeasure, UnitPrice, Is1099Item, Adjustment, PostingDate, GLTransactionID, WorkOrderNumber, VendorCredit, RecNextAmount, ManualVendorCredit, LongDescription, AmountApplied, PaymentAmount, RemainingBalance
- **Link**: rel, href
- **MailMatrix**: MailingMatrixID, Correspondence, EnabledBitMask, DefaultBitMask, Fixed, TemplateID, AllowOptOut, MakeMailMandatory, UserType, IsSet, Mail, Email, RefID
- **MailMatrixUpdate**: MailingMatrixID, Mail, Email, RefID
- **Note**: NoteID, RefType, RefID, CategoryName, CategoryID, Type, Note, NoteDate, BoardMembersOK, InternalViewOnly, Author, Recurring, IsDeleted, DateCreated, LastModified, Links, CreatedByName
- **Object**: 
- **OptOutOptions**: RefID, RefType, NameEnabled, MailingAddressEnabled, UnitAddressEnabled, EmailEnabled, PhotoEnabled, PhoneEnabled
- **PasswordChange**: NameOption, NewPassword
- **Payment**: PaymentID, ClientID, ClientName, PaymentGLAccountID, PaymentGLAccount, PayeeName, PayeeType, PayeeTypeString, PayeeID, CheckNumberSeries, CheckNumber, Amount, PaymentDate, Memo, PayerAddress, RemitAddress, MailingAddress, PayeeAddress, Printed, GLTransactionID, APBasis, CheckImage, StubImage, Voided, VoidGLTransactionID, BatchID, PaymentCCID, PaymentCostCenter, CentralDisbursmentApplied, FromAPI, PaymentType, AcceptedAPI, ACHBatchID, ACHCommitted, IsDeleted, DateCreated, LastModified, Links, Invoices, InvoiceIDs, AppliedPayments, PostedCheckNumber, PaymentInvoices, ManualPayment, Reconciled, PositivePay
- **PaymentInvoice**: InvoiceID, LineItems, PaymentAmount
- **PaymentLineItem**: LineItemID, PaymentAmount
- **PaymentVoid**: Reason, PostingDate
- **PendingArcStep**: StepID, StepType, StepText, StepLongText, Requirement
- **Person**: RefType, RefID, NameOption, Name, ManagementCompanyID, AccountExists, Email, AccountNumber
- **Pet**: PetID, ContactID, Name, Type, Breed, LicenseNumber, Size, Notes, IsDeleted, DateCreated, LastModified, Links
- **Phone**: PhoneID, RefType, RefID, PhoneType, PhoneTypeName, AreaCode, Number, Extension, IsPrimary, IsSecondary, NameOption, IsDeleted, DateCreated, CreatedBy, LastModified, ModifiedBy
- **PostingFine**: PostingDate, Amount, Description, UnitAccountID, ClientID, RefNumber, SupportingText
- **RecoverUsernameObject**: AccountNumber, Email
- **RequestNewUserAccountConfirmObject**: GUID, Username, Password
- **RequestNewUserAccountObject**: AccountNumber, Email, RefType, RefID, NameOption, URLForEmailLink, UnitAddress, UnitNumber
- **ResetPasswordConfirmObject**: GUID, Password
- **ResetPasswordObject**: Username, Email, AccountNumber, URLForEmailLink
- **ServiceRequest**: GroupID, CreatedByName, IsContact, RefType, RefID, Location, Notes, KBCatID, KBItemID, CreatedBy, ProblemID, CreatedByContactID, CreatedByNameOption
- **Vendor**: VendorID, VendorType, CompanyName, VendorCode, Location, PrimaryContactName, Phone, Mobile, Fax, Email, Website, Address1, Address2, City, County, State, Zip, Country, RemitAddress1, RemitAddress2, RemitCity, RemitState, RemitZip, RemitCountry, SameAsLocation, VAcctNumber, EIN, StateTaxID, VAcctTypeID, AcctTermsID, CreditLimit, CheckDisplayName, PaymentTypesAccepted, Requires1099, Type1099, BusinessLicense, ContractorLicense, EDDRequired, EDDReported, IsSoleProprietor, SoleProprietorName, SSN, IsActive, DBA, CombinePayments, InsuranceExempt, ACHBankName, ACHAccountNumber, ACHRoutingNumber, MaintenanceCompany, Facebook, Twitter, LinkedIn, IsDeleted, DateCreated, LastModified, ActivityTypes, MailMatrix, Insurance, Links
- **Vendor1099Adjustment**: VendorID, ClientID, Amount, PostingDate, Description, IsDeleted, DateCreated, LastModified
- **VendorContact**: VContactID, VendorID, Name, Title, IsPrimary, MaintenanceCompany, HourlyRate, Phone, Mobile, Fax, Email, IsDeleted, DateCreated, LastModified
- **ViolationImageRequest**: PicRecType, RefID, RefType, Caption, DisplayOrder, Version, Author, UserID, Image
- **ViolationNote**: ViolationID, CategoryID, InternalViewOnly, BoardMembersOK, Note
