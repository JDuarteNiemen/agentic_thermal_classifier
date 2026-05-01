# This Script contains the function that establishes the literature bank for the LLM to read
import json
import re
import requests
import textwrap
import xml.etree.ElementTree as ET
from lxml import etree
import subprocess
from time import sleep

def FetchNcbiMetadata(accession: str) -> dict:
    """
    Fetch metadata for a protein record from NCBI using an accession number.
    Returns a flat dictionary of key metadata fields.
    """

    # Step 1: Search for the UID corresponding to the accession
    params = {
        "db": "protein",
        "term": accession,
        "retmode": "json",
    }
    search = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params=params)
    uid = search.json()["esearchresult"]["idlist"][0]
    sleep(0.3)

    # Step 2: Fetch the full summary record using the UID
    fetch = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", params={
        "db": "protein",
        "id": uid,
        "retmode": "json",
    })
    sleep(0.3)

    rec = fetch.json()["result"]
    res = rec.get(rec["uids"][0])

    # subtype/subname are pipe-delimited strings encoding key-value feature pairs
    # e.g. subtype="strain|country" subname="H1N1|USA" -> {"strain": "H1N1", "country": "USA"}
    subtype = res.get("subtype")
    subname = res.get("subname")

    record = {
        "uid": res.get("uid"),
        "accession": res.get("caption"),
        "title": res.get("title"),
        "organism": res.get("organism"),
        "taxonId": res.get("taxid"),
        "sequence_length": res.get("slen"),
        "create_date": res.get("createdate"),
        "update_date": res.get("updatedate"),
        "dbsource": res.get("sourcedb"),
        "extra": res.get("extra"),
    }

    # Unpack subtype/subname pairs into top-level record keys (if present)
    if subtype and subname:
        type_parts = subtype.split("|")
        name_parts = subname.split("|")
        for t, n in zip(type_parts, name_parts):
            if t and n:
                record[t] = n

    return record



def WriteJson(meta, save_dir):
    with open(f'{save_dir}.json', 'w') as f:
        json.dump(meta, f)



# Getting all pmcids associated with an accession

def FetchPMIDS(accession: str) -> list[dict]:
    """
    Given a protein accession, return associated PubMed ids.
    """

    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    # Step 1: Get UID from accession
    search = requests.get(base + "esearch.fcgi", params={
        "db": "protein",
        "term": accession,
        "retmode": "json",
    }).json()
    sleep(0.3)

    ids = search.get("esearchresult", {}).get("idlist", [])

    if not ids:
        return []
    uid = ids[0]

    # Step 2: Link to PubMed
    link = requests.get(base + "elink.fcgi", params={
        "dbfrom": "protein",
        "db": "pubmed",
        "id": uid,
        "retmode": "json",
    }).json()
    sleep(0.3)
    try:
        pmids = link["linksets"][0]["linksetdbs"][0]["links"]
    except (KeyError, IndexError):
        return []
    if not pmids:
        return []

    # Step 3: Fetch PubMed summaries
    summaries = requests.get(base + "esummary.fcgi", params={
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
    }).json()
    sleep(0.3)

    return pmids




def FetchLiteraturePMID(pmid: str) -> str | None:
    """
    Return the abstract text for a given PMID.
    Returns None if no abstract is available.
    """

    res = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
        params={
            "db": "pubmed",
            "id": pmid,
            "retmode": "xml",
        },
    )
    sleep(0.3)



    return res.text





def PMID2PMCID(pmid: str) -> str | None:

    url = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"

    res = requests.get(
        url,
        params={
            "ids": pmid,
            "format": "json"
        },
        timeout=10
    )
    sleep(0.5)

    if res.status_code != 200:
        return None
    try:
        data = res.json()
    except ValueError:
        return None
    records = data.get("records", [])

    if not records:
        return None
    return records[0].get("pmcid")

def DownloadPaper(pmcid, save_dir):
    aws='/usr/local/bin/aws'


    out=subprocess.run(f'{aws} --no-sign-request s3 ls s3://pmc-oa-opendata/{pmcid}.1/', shell=True, capture_output=True, text=True)
    if f'{pmcid}.1.txt' not in out.stdout and f'{pmcid}.1.pdf' not in out.stdout:
        print(f'No txts or PDFs found for this paper: {pmcid}')
        print(out)
        return None

    if f'{pmcid}.1.txt' in out.stdout:
        file_type = 'txt'
    elif f'{pmcid}.1.pdf' in out.stdout:
        file_type = 'pdf'

    #Download paper3
    subprocess.run(f'{aws} --no-sign-request  s3 cp s3://pmc-oa-opendata/{pmcid}.1/{pmcid}.1.{file_type} {save_dir}', shell=True)


def CleanXml(xml_text: str) -> dict | None:

    parser = etree.XMLParser(recover=True)

    root = etree.fromstring(xml_text.encode(), parser)

    # --- Title ---
    title_elem = root.find(".//ArticleTitle")
    title = "".join(title_elem.itertext()).strip() if title_elem is not None else None

    # --- Abstract ---

    abstract_parts = []
    for elem in root.findall(".//AbstractText"):
        text = "".join(elem.itertext()).strip()
        if text:
            abstract_parts.append(text)
    abstract = " ".join(abstract_parts) if abstract_parts else None
    if not title and not abstract:
        return None

    return {
        "title": title,
        "abstract": abstract
    }


def SearchPubmed(query: str, max_results: int = 20) -> list[str]:
    """
    Search PubMed using a text query and return a list of PMIDs.
    """
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    res = requests.get(url, params={
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results
    }).json()
    sleep(0.3)

    return res.get("esearchresult", {}).get("idlist", [])



def WritePaper(paper, save_dir):
    width = 100
    with open(save_dir, 'w') as f:
        f.write(paper['title'] + "\n\n")
        wrapped = textwrap.fill(paper['abstract'], width=width)
        f.write(wrapped)


# Get pmids from accession
# If possible convert pmid to pmcid
# If not possible get paper using pmid -> store paper (try clean it)
# If no literature found, query search pubmed using search terms obtained from ncbi metadata.
import os


def CreateLibrary(accession, meta):
    # Make dirs to accept papers
    os.makedirs(f'data/library/{accession}', exist_ok=True)

    # Extract metadata if not already passed
    if not meta:
        meta = FetchNcbiMetadata(accession)

    species = meta.get('organism')


    pmids = FetchPMIDS(accession)  # get PMIDS associated with accession
    if pmids:
        for pmid in pmids:
            pmcid = PMID2PMCID(pmid)
            if not pmcid:  # No PMCID avaliable
                paper = FetchLiteraturePMID(pmid)  # Fetch abstract from pmid
                paper = CleanXml(paper)  # clean it and write it to a text file.
                WritePaper(paper, f'data/library/{accession}/{pmid}.txt')
            if pmcid: # pmid converted to pmcid
                DownloadPaper(pmcid, f'data/library/{accession}/') # download the paper
    else:
        pmids = SearchPubmed(species) # query search species name
        for pmid in pmids:
            pmcid = PMID2PMCID(pmid) #convert pmid to pmcid
            if not pmcid: # not convertable
                paper = FetchLiteraturePMID(pmid) #get abstract from pmid
                paper = CleanXml(paper) #clean and write it to file
                WritePaper(paper, f'data/library/{accession}/{pmid}.txt')
            if pmcid:
                DownloadPaper(pmcid, f'data/library/{accession}/')

def HostLibrary(accesion, host):
    os.makedirs(f'data/library/{accesion}/host', exist_ok=True)

    pmids = SearchPubmed(host)
    for pmid in pmids:
        pmcid = PMID2PMCID(pmid)
        if not pmcid:
            paper = FetchLiteraturePMID(pmid)
            paper = CleanXml(paper)
            WritePaper(paper, f'data/library/{accesion}/host/{pmid}.txt')
        if pmcid:
            DownloadPaper(pmcid, f'data/library/{accesion}/host/')


def RankPapers(paper_dir, patterns):

    papers = os.listdir(paper_dir)
    paper_rankings = {}
    for paper in papers:

        with open(f'{paper_dir}/{paper}', 'r') as f:
            text = f.read()

        paper_length = len(text)

        matches = {}

        for label, pattern in patterns.items():
            matches[label] = len(re.findall(pattern, text, re.IGNORECASE))

        matches['total'] = sum(matches.values())
        matches['normalised'] = (sum(matches.values()) / paper_length)

        paper_rankings[paper] = matches

    sorted_papers = sorted(
        paper_rankings.items(),
        key=lambda x: x[1]["total"],
        reverse=True
    )
    sorted_dict = dict(sorted_papers)

    return sorted_dict