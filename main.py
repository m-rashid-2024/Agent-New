
import requests
import json
import os
import logging as log_root
from ollama import Client

import src.utils.log_level_converter as log_level_converter

log_root.basicConfig(
    level=log_level_converter.convert_string_to_logger_level(os.getenv("logger_level")),
    format='%(asctime)s - %(name)s - [%(levelname)s]: %(message)s', datefmt="%H:%M:%S")

log = log_root.getLogger(__name__)

# set global vars
ollama_host = os.getenv("ollama_host")
ollama_model = os.getenv("ollama_model")
username = os.getenv("username")
password = os.getenv("password")

ollama_client = Client(
  host=ollama_host
)

def get_access_token() -> str:
  payload = {
    'grant_type': 'password',
    'client_id': 'optadata-care',
    'username': username,
    'password': password
  }
  response = requests.post("https://login.login-one.de/auth/realms/one/protocol/openid-connect/token",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data=payload)
  return response.json()["access_token"]


def get_client_id(firstname: str, lastname: str) -> str:
  token = get_access_token()
  log.debug("get_client_id function called with: " + firstname + " " + lastname + "")

  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/klient", headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_client_id function called with: " + firstname + " " + lastname + "")
    return "error at api call"

  #type dict
  clients = json.loads(data.text)

  for client in clients["content"]:
    if client["person"]["name"] == lastname and client["person"]["vorname"] == firstname:
      return str(client["id"])

  log.info("Client not found")
  return "Client not found"


def get_client_document_id(client_id: str, document_typ: str) -> str:
  token = get_access_token()
  log.debug("get_client_document_id function called with: " + client_id + " " + document_typ + "")

  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/klient/" + client_id + "/pflegedoku", headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_client_document_id function called with: " + client_id + " " + document_typ + "")
    return "error at api call"

  #type dict
  documents = json.loads(data.text)

  for document in documents["pflegedokuList"]:
    if document["dokumenttyp"] == document_typ:
      for document_entry in document["dokumente"]:
        match document_entry["status"]:
          case "FREIGEGEBEN" | "EVALUIERT" | "ANLAGE" | "ABGESCHLOSSEN" | "NEUANLAGE":
            return str(document_entry["id"])
          case _:
            log.info("document status not found")
            return "document status not found"

  log.info("document not found")
  return "document not found"


def get_client_data(firstname: str, lastname: str) -> str:
  """
  Gibt den Wohnort zu Klienten aus

  Args:
    firstname: Vorname des clienten
    lastname: Nachname des clienten

  Returns:
    str: Wohnort des clienten
  """

  token = get_access_token()
  log.debug("get_client_data function called with: " + firstname + " " + lastname + "")

  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/klient", headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_client_data function called with: " + firstname + " " + lastname + "")
    return "error at api call"

  #type dict
  clients = json.loads(data.text)

  for client in clients["content"]:
    if client["person"]["name"] == lastname and client["person"]["vorname"] == firstname:
      return str(client)

  log.info("Client not found")
  return "Client not found"



def get_berichteblatt(firstname: str, lastname: str) -> str:
  """
  Gibt einen Bericht zu einer Person zurück

  Args:
    firstname: Vorname des Klienten
    lastname: Nachname des Klienten

  Returns:
    str: Bericht zum Klienten
  """

  log.debug("get_berichteblatt function called with: " + firstname + " " + lastname + "")

  client_id = get_client_id(firstname, lastname)
  document_id = get_client_document_id(client_id, 'BERICHTEBLATT')

  token = get_access_token()
  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/berichteblatteintrag/" + document_id, headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_berichteblatt function called with: " + firstname + " " + lastname + "")
    return "error at api call"

  #type list
  report_entries = json.loads(data.text)
  combined_entries = ""
  for eintrag in report_entries:
    combined_entries = combined_entries + "\n" + " " + eintrag["content"]["bericht"] + ". "

  if not combined_entries:
    log.info("No report entries found")
    return "No report entries found"

  return combined_entries



def get_vitalwerte(firstname: str, lastname: str) -> str:
  """
  Gibt die Vitalwerte zu einer Person zurück

  Args:
    firstname: Vorname des Klienten
    lastname: Nachname des Klienten

  Returns:
    str: Vitalwerte zur Person
  """

  log.debug("get_vitalwerte function called with: " + firstname + " " + lastname + "")

  client_id = get_client_id(firstname, lastname)
  document_id = get_client_document_id(client_id, 'VITALWERTE')

  token = get_access_token()
  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/vitalwerte/" + document_id, headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_vitalwerte function called with: " + firstname + " " + lastname + "")
    return "error at api call"

  #type dict
  vital_values = json.loads(data.text)

  if vital_values["vitalwerteintraege"] is None:
    log.info("No vital values found")
    return "No vital values found"
  else:
    return str(vital_values["vitalwerteintraege"][0])

def get_fluessigkeitbilanz(firstname: str, lastname: str) -> str:
  """
  Gibt die Fluessigkeitsbilanz zu einer Person zurück

  Args:
    firstname: Vorname des Klienten
    lastname: Nachname des Klienten

  Returns:
    str: Fluessigkeitsbilanz zum Klienten
  """

  log.debug("get_fluessigkeitbilanz function called with: " + firstname + " " + lastname + "")

  client_id = get_client_id(firstname, lastname)
  document_id = get_client_document_id(client_id, 'FLUESSIGKEITSBILANZIERUNG')

  token = get_access_token()
  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/fluessigkeitsbilanzierung/" + document_id + "/alle-eintraege", headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_fluessigkeitbilanz function called with: " + firstname + " " + lastname + "")
    return "error at api call"

  #type list
  fluid_intake_data = json.loads(data.text)

  combined_entries = ""
  for entry in fluid_intake_data:
    for sub_entry in entry["subEintraege"]:
      combined_entries = (combined_entries + "\n" + firstname + " " + lastname + " hat " + str(sub_entry["content"]["einfuhrmenge"]) + " ml " +
                          str(sub_entry["content"]["fluessigkeit"]) + " getrunken. Er hat " + str(sub_entry["content"]["ausfuhrmenge"]) +
                          " ml " + str(sub_entry["content"]["fluessigkeit"]) +" ausgeschieden.")

    if not combined_entries:
      log.info("No fluid intake data found")
      return "No fluid intake data found"

    return combined_entries

def get_ernaehrung(firstname: str, lastname: str) -> str:
  """
  Gibt einen Ernaerungsbericht zu einer Person zurück

  Args:
    firstname: Vorname des Klienten
    lastname: Nachname des Klienten

  Returns:
    str: Ernaehrung oral des Klienten
  """

  log.debug("get_ernaehrung function called with: " + firstname + " " + lastname + "")

  client_id = get_client_id(firstname, lastname)
  document_id = get_client_document_id(client_id, 'ERNAEHRUNG_ORAL')

  token = get_access_token()
  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/ernaehrung-oral/" + document_id + "/alle-eintraege", headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_ernaehrung function called with: " + firstname + " " + lastname + "")
    return "error at api call"

  #type list
  oral_nutrition = json.loads(data.text)

  combined_entries = ""
  for entry in oral_nutrition:
    for sub_entry in entry["subEintraege"]:
      combined_entries = (combined_entries + "\n" + firstname + " " + lastname + " hat " + str(sub_entry["content"]["mahlzeit"]) + " als " +
                          str(sub_entry["content"]["lebensmittel"]) + " gegessen. Er hat dadurch " + str(sub_entry["content"]["kcal"]) +
                          " Kalorie/n zu sich genommen.")

    if not combined_entries:
      log.info("No oral nutrition found")
      return "No oral nutrition found"

    return combined_entries

# Medikationsplan
def get_medikationsplan(firstname: str, lastname: str) -> str:
  """
  Gibt einen Medikationsplan zu einer Person zurück

  Args:
    firstname: Vorname des Klienten
    lastname: Nachname des Klienten

  Returns:
    str: Medikationsplan zum Klienten
  """

  log.debug("get_medikationsplan function called with: " + firstname + " " + lastname + "")

  #medikationsplan_id = "56d318a0-dbd4-41a7-8fb1-827469eaba19"
  client_id = get_client_id(firstname, lastname)
  document_id = get_client_document_id(client_id, "MEDIKATIONSPLAN")

  token = get_access_token()
  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/medikationsplaneintrag/" + document_id, headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_medikationsplan function called with: " + firstname + " " + lastname + "")
    return "error at api call"

  #if data.status_code == 200:
    #return "Success at api call"
  #else: print(data.status_code)

  #type list
  medication_plan = json.loads(data.text)

  combined_entries = ""
  for entry in medication_plan:
     combined_entries = (combined_entries + "\n" + firstname + " " + lastname + " bekommt " + str(entry["content"]["handelsname"]) + " als Medikamente " +
                       str(entry["content"]["einheit"]) + " täglich. Die Medikamente nimmt " + firstname + " als " + str(entry["content"]["typ"]) + ".")

  if not combined_entries:
    log.info("No medication plan found")
    return "No medication plan found"

  return combined_entries

def get_massnahmenplan(firstname: str, lastname: str) -> str:
  """
  Gibt einen Maßnahmenplan zu einer Person zurück

  Args:
    firstname: Vorname des Klienten
    lastname: Nachname des Klienten

  Returns:
    str: Massnahmenplan zum Klienten
  """

  log.debug("get_massnahmenplan function called with: " + firstname + " " + lastname + "")

  client_id = get_client_id(firstname, lastname)
  document_id = get_client_document_id(client_id, 'MASSNAHMENPLAN')

  token = get_access_token()
  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/massnahmenplan/" + document_id + "/alle-eintraege", headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_massnahmenplan function called with: " + firstname + " " + lastname + "")
    return "error at api call"

  #type list
  measure_plan = json.loads(data.text)

  combined_entries = ""
  for entry in measure_plan:
    for content in entry["massnahmen"]:
        combined_entries = (combined_entries + " \n" +  content["content"]["text"] + ". ")

  if not combined_entries:
    log.info("No measure plan found")
    return "No measure plan found"

  return combined_entries

def get_biografie(firstname: str, lastname: str) -> str:
  """
  Gibt die Biografie zu einer Person zurück

  Args:
    firstname: Vorname des Klienten
    lastname: Nachname des Klienten

  Returns:
    str: Biografie zum Klienten in JSON Format
  """

  log.debug("get_biografie function called with: " + firstname + " " + lastname + "")

  client_id = get_client_id(firstname, lastname)
  document_id = get_client_document_id(client_id, "BIOGRAFIEBOGEN")

  token = get_access_token()
  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/biografiebogen/" + document_id, headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_biografie function called with: " + firstname + " " + lastname + "")
    return "error at api call"

  #type dict
  biografie = json.loads(data.text)

  combined_entries = ""
  for entry, content in biografie.items():
    if isinstance(content, dict):
      for current_index in content:
        if content[current_index] is None:
          continue
        combined_entries = (combined_entries + " \n" + content[current_index] + ". ")

  if not combined_entries:
    log.info("No biografie found")
    return "No biografie found"

  return combined_entries



def get_sis_ambulant(firstname: str, lastname: str) -> str:
  """
  Gibt ambulante Informationen zu einer Person zurück

  Args:
    firstname: Vorname des Klienten
    lastname: Nachname des Klienten

  Returns:
    str: Ambulant Informationen zum Klienten in JSON Format
  """
  #medikationsplan_id = "56d318a0-dbd4-41a7-8fb1-827469eaba19"
  #sis_ambulant_id = "41bc7176-a264-404d-a5fe-d56ed82b8c2b"

  log.debug("get_sis_ambulant function called with: " + firstname + " " + lastname + "")

  client_id = get_client_id(firstname, lastname)
  document_id = get_client_document_id(client_id, "SIS_AMBULANT")

  token = get_access_token()
  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/sis-ambulant/" + document_id, headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_sis_ambulant function called with: " + firstname + " " + lastname + "")
    return "error at api call"

  #type dict
  result = json.loads(data.text)

  return result


def get_current_needs(firstname: str, lastname: str) -> str:
  """
  Gets the current needs of a client from the sis ambulant tool.
  Args:
    firstname: firstname of the client.
    lastname: lastname of the client.

  Returns:
    str: The current needs of the client.

  """

  log.debug("get_current_needs function called with: " + firstname + " " + lastname + "")

  client_id = get_client_id(firstname, lastname)
  document_id = get_client_document_id(client_id, "SIS_AMBULANT")

  token = get_access_token()
  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/sis-ambulant/" + document_id, headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_current_needs function called with: " + firstname + " " + lastname + "")
    return "error at api call"

  #type dict
  ambulant_info = json.loads(data.text)

  current_needs = ""

  for entry, content in ambulant_info.items():
    if isinstance(content, dict):
      for current_index in content:
        if content[current_index] is None:
          continue
        if current_index == "momentanerStandpunkt":
          current_needs = content[current_index]

  if not current_needs:
    log.info("No current needs found")
    return "No current needs found"

  return current_needs

def get_cognitive_and_communicative_skills(firstname: str, lastname: str) -> str:
  """
  Gets the cognitive and communicative skills of a client from the sis ambulant tool.
  Args:
    firstname: firstname of the client.
    lastname: lastname of the client.

  Returns:
    str: The cognitive and communicative skills of the client.

  """

  log.debug("get_cognitive_and_communicative_skills function called with: " + firstname + " " + lastname + "")

  client_id = get_client_id(firstname, lastname)
  document_id = get_client_document_id(client_id, "SIS_AMBULANT")

  token = get_access_token()
  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/sis-ambulant/" + document_id, headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_cognitive_and_communicative_skills function called with: " + firstname + " " + lastname + "")
    return "error at api call"

  #type dict
  ambulant_info = json.loads(data.text)

  client_skills = ""

  for entry, content in ambulant_info.items():
    if isinstance(content, dict):
      for current_index in content:
        if content[current_index] is None:
          continue
        if current_index == "themenfeld1":
          client_skills = content[current_index]

  if not client_skills:
    log.info("No cognitive and communicative skills found")
    return "No cognitive and communicative skills found"

  return client_skills

def get_mobility_and_agility_skills(firstname: str, lastname: str) -> str:
  """
  Gets the mobility and agility skills of a client from the sis ambulant tool.
  Args:
    firstname: firstname of the client.
    lastname: lastname of the client.

  Returns:
    str: The mobility and agility skills of the client.

  """

  log.debug("get_mobility_and_agility_skills function called with: " + firstname + " " + lastname + "")

  client_id = get_client_id(firstname, lastname)
  document_id = get_client_document_id(client_id, "SIS_AMBULANT")

  token = get_access_token()
  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/sis-ambulant/" + document_id, headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_mobility_and_agility_skills function called with: " + firstname + " " + lastname + "")
    return "error at api call"

  #type dict
  ambulant_info = json.loads(data.text)

  client_skills = ""

  for entry, content in ambulant_info.items():
    if isinstance(content, dict):
      for current_index in content:
        if content[current_index] is None:
          continue
        if current_index == "themenfeld2":
          client_skills = content[current_index]

  if not client_skills:
    log.info("No mobility and agility skills found")
    return "No mobility and agility skills found"

  return client_skills

def get_illness_related_demands_and_stresses(firstname: str, lastname: str) -> str:
  """
  Gets the illness-related demands and stresses of a client from the sis ambulant tool.
  Args:
    firstname: firstname of the client.
    lastname: lastname of the client.

  Returns:
    str: The illness-related demands and stresses of the client.

  """

  log.debug("get_illness_related_demands_and_stresses function called with: " + firstname + " " + lastname + "")

  client_id = get_client_id(firstname, lastname)
  document_id = get_client_document_id(client_id, "SIS_AMBULANT")

  token = get_access_token()
  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/sis-ambulant/" + document_id, headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_illness_related_demands_and_stresses function called with: " + firstname + " " + lastname + "")
    return "error at api call"

  #type dict
  ambulant_info = json.loads(data.text)

  illness_related_demands_and_stresses = ""

  for entry, content in ambulant_info.items():
    if isinstance(content, dict):
      for current_index in content:
        if content[current_index] is None:
          continue
        if current_index == "themenfeld3":
          illness_related_demands_and_stresses = content[current_index]

  if not illness_related_demands_and_stresses:
    log.info("No illness-related demands and stresses found")
    return "No illness-related demands and stresses found"

  return illness_related_demands_and_stresses

def get_self_sufficiency(firstname: str, lastname: str) -> str:
  """
  Gets the self-sufficiency of a client from the sis ambulant tool.
  Args:
    firstname: firstname of the client.
    lastname: lastname of the client.

  Returns:
    str: The self-sufficiency of the client.

  """

  log.debug("get_self_sufficiency function called with: " + firstname + " " + lastname + "")

  client_id = get_client_id(firstname, lastname)
  document_id = get_client_document_id(client_id, "SIS_AMBULANT")

  token = get_access_token()
  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/sis-ambulant/" + document_id, headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_self_sufficiency function called with: " + firstname + " " + lastname + "")
    return "error at api call"

  #type dict
  ambulant_info = json.loads(data.text)

  self_sufficiency = ""

  for entry, content in ambulant_info.items():
    if isinstance(content, dict):
      for current_index in content:
        if content[current_index] is None:
          continue
        if current_index == "themenfeld4":
          self_sufficiency = content[current_index]

  if not self_sufficiency:
    log.info("No self-sufficiency found")
    return "No self-sufficiency found"

  return self_sufficiency

def get_social_relationships(firstname: str, lastname: str) -> str:
  """
  Gets the social_relationships of a client from the sis ambulant tool.
  Args:
    firstname: firstname of the client.
    lastname: lastname of the client.

  Returns:
    str: The social_relationships of the client.

  """

  log.debug("get_social_relationships function called with: " + firstname + " " + lastname + "")

  client_id = get_client_id(firstname, lastname)
  document_id = get_client_document_id(client_id, "SIS_AMBULANT")

  token = get_access_token()
  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/sis-ambulant/" + document_id, headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_social_relationships function called with: " + firstname + " " + lastname + "")
    return "error at api call"

  #type dict
  ambulant_info = json.loads(data.text)

  social_relationships = ""

  for entry, content in ambulant_info.items():
    if isinstance(content, dict):
      for current_index in content:
        if content[current_index] is None:
          continue
        if current_index == "themenfeld5":
          social_relationships = content[current_index]

  if not social_relationships:
    log.info("No social_relationships found")
    return "No social_relationships found"

  return social_relationships

def get_household_management(firstname: str, lastname: str) -> str:
  """
  Gets the household_management of a client from the sis ambulant tool.
  Args:
    firstname: firstname of the client.
    lastname: lastname of the client.

  Returns:
    str: The household_management of the client.

  """

  log.debug("get_household_management function called with: " + firstname + " " + lastname + "")

  client_id = get_client_id(firstname, lastname)
  document_id = get_client_document_id(client_id, "SIS_AMBULANT")

  token = get_access_token()
  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/sis-ambulant/" + document_id, headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_household_management function called with: " + firstname + " " + lastname + "")
    return "error at api call"

  #type dict
  ambulant_info = json.loads(data.text)

  household_management = ""

  for entry, content in ambulant_info.items():
    if isinstance(content, dict):
      for current_index in content:
        if content[current_index] is None:
          continue
        if current_index == "themenfeld6":
          household_management = content[current_index]

  if not household_management:
    log.info("No household_management found")
    return "No household_management found"

  return household_management
    
# new function for accident report
def get_accident_report(firstname: str, lastname: str) -> str:
  """
  Gibt das Sturzprotokoll zu einer Person zurück

  Args:
    firstname: Vorname des Klienten
    lastname: Nachname des Klienten

  Returns:
    str: Sturzprotokoll Information zur Person
  """

  log.debug("get_accident_report function called with: " + firstname + " " + lastname + "")

  client_id = get_client_id(firstname, lastname)
  document_id = get_client_document_id(client_id, 'STURZPROTOKOLL')

  token = get_access_token()
  headers = {"Authorization": "Bearer " + token}
  data = requests.get("https://api.optadatacare.de/api/fe/sturzprotokoll/" + document_id, headers=headers)

  if data.status_code != 200:
    log.error("Error at api call - " + str(data.status_code) + " get_accident_report function called with: " + firstname + " " + lastname + "")
    return "error at api call"

  accident_report_info = json.loads(data.text)

# type Dictionary
  report_info = ""
  for content in accident_report_info.values():
    if isinstance(content, dict):
      for value in content:
        if content[value] is None:
          continue
        report_info = report_info + "\n" + content[value] + "."
  return report_info


def agent(messages: list) -> list:

  # Findet das richtige Tool zur Anfrage
  response = ollama_client.chat(
    model=ollama_model,
    messages=messages,
    tools=[get_client_data, get_berichteblatt, get_vitalwerte, get_fluessigkeitbilanz,
           get_ernaehrung, get_medikationsplan,get_massnahmenplan, get_sis_ambulant,
           get_current_needs,get_cognitive_and_communicative_skills,get_mobility_and_agility_skills,
           get_illness_related_demands_and_stresses,get_self_sufficiency,
           get_social_relationships,get_household_management, get_biografie, get_accident_report]
  )

  result = ""
  for tool in response.message.tool_calls or []:
    kwargs = tool.function.arguments
    result = result + " " + getattr(__import__("__main__"), tool.function.name)(**kwargs)
    log.info("Ergebnis des Tools " + tool.function.name + ":" + result)
    message = {"role": "tool", "tool_call_id": tool.function.name, "content": result}
    messages.append(message)

  # Formuliert eine Antwort mit den Informationen aus den Tools
  response = ollama_client.chat(
    model=ollama_model,
    messages=messages
  )

  message = {"role": "assistant", "content": response["message"]["content"]}
  messages.append(message)
  log.info("Antwort des Assistants: " + message["content"])
  return messages

#print(agent("Gib einen Bericht über Lukas Meister aus ?"))
#print(agent("Welche Vitalwerte hat Lukas Meister ?"))
#print(agent("Welche Fluessigkeitsbilanzierung hat Lukas Meister ?"))
#print(agent("Was hat Lukas Meister gestern gegessen ?"))
#print(agent("Welche Medikamente bekommt Lukas Meister ?"))
#print(agent("Welche Maßnahmen sind für Lukas Meister vorgesehen ?"))
#print(agent("In wie weit ist Lukas Meister in seiner Bewegung oder Mobilität eingeschränkt?"))

messages=[
    {"role": "system", "content": "Du bist ein hilfreicher Assistent und beantwortest Fragen von Benutzer. Dazu nutzt du Informationen aus den Tools."},
    {"role": "user", "content": "Welche Medikamente bekommt Lukas Meister und welche Maßnahmen sind für ihn vorgesehen?"},
    {"role": "tool", "tool_call_id": "get_client_id", "content": "Lukas Meister hat die ID 61a4f89e-6d6d-4fc5-842e-42d66ce51d45"},
    {"role": "tool", "tool_call_id": "get_medikationsplan", "content": "Lukas Meister bekommt Bisoprolol als Medikamente STUECK_1 täglich. Die Medikamente nimmt Lukas als DAUERMEDIKATION. Lukas Meister bekommt Paracetamol als Medikamente STUECK_1 täglich. Die Medikamente nimmt Lukas als DAUERMEDIKATION."},
    {"role": "tool", "tool_call_id": "get_massnahmenplan", "content": "Jeden morgen muss Lukas 10 Liegestütze machen. Jeden Mittag muss Lukas Proteine zu sich nehmen. Abends muss Lukas 10 Klimmzüge machen."},
    {"role": "assistant", "content": "Lukas Meister bekommt täglich Bisoprolol und Paracetamol. Jeden morgen muss Lukas 10 Liegestütze machen. Jeden Mittag muss Lukas Proteine zu sich nehmen. Abends muss Lukas 10 Klimmzüge machen."},
    {"role": "user", "content": "Hat Lukas Meister ein Sturzprotokoll?"},
  ]

log.info("agent messages: %s", agent(messages))
