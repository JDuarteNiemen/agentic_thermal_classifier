import requests

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

    # Step 2: Fetch the full summary record using the UID
    fetch = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", params={
        "db": "protein",
        "id": uid,
        "retmode": "json",
    })

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


def pmid_to_pmcid(pmid: str) -> str | None:

    """

    Convert a single PMID to a PMCID.

    Returns the PMCID (e.g. 'PMC1234567') or None if not available.

    """

    url = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"

    res = requests.get(url, params={

        "ids": pmid,

        "format": "json"

    }).json()

    records = res.get("records", [])

    if not records:

        return None

    return records[0].get("pmcid")

def FetchLiterature(accession: str) -> list[dict]:
    """
    Given a protein accession, return associated PubMed articles.
    Each article is returned as a dictionary with key metadata.
    """

    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    # Step 1: Get UID from accession
    search = requests.get(base + "esearch.fcgi", params={
        "db": "protein",
        "term": accession,
        "retmode": "json",
    }).json()

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
    results = summaries.get("result", {})




    papers = []
    for pmid in pmids:
        pmcid = pmid_to_pmcid(pmid)
        paper = results.get(pmid)
        if not paper:
            continue
        papers.append({
            "pmcid": pmcid,
            "title": paper.get("title"),
            "authors": [a["name"] for a in paper.get("authors", [])],
            "journal": paper.get("fulljournalname"),
            "pubdate": paper.get("pubdate"),
        })

    literature={}
    for paper in papers:
        pmid=paper['pmid']
        title = paper.get("title")
        res = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
        params={
            "db": "pubmed",
            "id": pmid,
            "retmode": "xml"},
    )
        literature[title]=res.text

    return literature