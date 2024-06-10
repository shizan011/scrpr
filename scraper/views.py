# views.py
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from .forms import UserLoginForm, ScrapeForm
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor
import os
import concurrent.futures

api_key = 'AIzaSyASyu2ro7rfJm8ceUILqiHooJMmH0wHdUM'
cse_id = 'e2e05413653094cff'

def google_search(query, api_key, cse_id, start, num_results=10):
    search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={cse_id}&start={start}&num={num_results}"
    response = requests.get(search_url)
    if response.status_code != 200:
        print(f"Failed to fetch search results: Status code {response.status_code}")
        return None
    results = response.json()
    return results

def extract_urls(results):
    if 'items' not in results:
        print("No items in search results.")
        return []
    urls = [item['link'] for item in results['items']]
    return urls

def clean_email(email):
    cleaned_email = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", email)
    if cleaned_email:
        return cleaned_email[0]
    return None

def fetch_url(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response

def scrape_emails_from_url(url):
    emails = []
    try:
        response = fetch_url(url)
        if response.status_code == 200:
            parsers = ['html.parser', 'html5lib', 'lxml']
            for parser in parsers:
                try:
                    soup = BeautifulSoup(response.content, parser)
                    break
                except Exception as e:
                    print(f"Error using {parser} parser: {e}. Trying next parser.")
            text = soup.get_text()
            raw_emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[a-zA-Z0-9./?=_-]*", text)
            for raw_email in raw_emails:
                cleaned_email = clean_email(raw_email)
                if cleaned_email:
                    emails.append(cleaned_email)
        else:
            print(f"Failed to fetch {url}: Status code {response.status_code}")
    except requests.HTTPError as e:
        print(f"Failed to fetch {url}: {e}")
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    return emails

def scrape_emails_from_urls(urls):
    all_emails = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(scrape_emails_from_url, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                emails = future.result()
                all_emails.extend(emails)
            except Exception as e:
                print(f"Error scraping {url}: {e}")
    return all_emails

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
    else:
        form = UserLoginForm()
    return render(request, 'scraper/login.html', {'form': form})

@login_required
def index(request):
    if request.method == 'POST':
        form = ScrapeForm(request.POST)
        if form.is_valid():
            location = form.cleaned_data['location']
            services = form.cleaned_data['services']
            email_providers = form.cleaned_data['email_providers']
            query = f'"{location}" "{services}" {email_providers}'
            
            total_results = 50  # Reduce total results to minimize the risk of hitting rate limits

            all_urls = []
            for start in range(1, total_results, 10):
                search_results = google_search(query, api_key, cse_id, start, num_results=10)
                if not search_results:
                    print("No search results found.")
                    break
                urls = extract_urls(search_results)
                all_urls.extend(urls)
                time.sleep(5)  # Increase the interval between queries

            all_emails = scrape_emails_from_urls(all_urls)

            unique_emails = list(set(all_emails))
            if unique_emails:
                df = pd.DataFrame(unique_emails, columns=["Email"])
                csv_path = os.path.join('static', 'emails.csv')
                df.to_csv(csv_path, index=False)
                request.session['emails'] = unique_emails
                return redirect('result')
            else:
                return render(request, 'scraper/index.html', {'form': form, 'error': 'No emails found.'})
    else:
        form = ScrapeForm()
    return render(request, 'scraper/index.html', {'form': form})

@login_required
def result(request):
    emails = request.session.get('emails', [])
    return render(request, 'scraper/result.html', {'emails': emails})

@login_required
def download_csv(request):
    csv_path = os.path.join('static', 'emails.csv')
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            response = HttpResponse(f, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=emails.csv'
            return response
    else:
        raise Http404("CSV file not found")
