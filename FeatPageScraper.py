import json, os, time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


class FeatPageScraper:

    def __init__(self, config_file_path:str, sleeper:int = 1, headless:bool = True, testing:bool = False):
        
        self.config_file_path = config_file_path
        self.config_folder_name = (os.path.basename(config_file_path)).replace('.json', '')
        self.config_folder_path = os.path.join("page_source_folder", self.config_folder_name)
        
        self.current_config_folder_path = ""  # config_folder_path + ymdh
        self.testing = testing
        self.headless = headless
        self.sleeper = sleeper # time to wait between page loads in seconds,
        
        # feat links are the links which are generated from the config file
        self.feat_links = []  
        self.page_source_paths = []  # paths to the folders that contain the page sources, eg.
        self.link_dict = {}  # stores links as values with html filenames (slightly modified) as keys
        self.links = []

    def generate_links_from_config_json(self) -> list[str]:

        """
        This function generates the links from the config file.

        :param config_file_path: Path to the config file.
        :return: List of links.
        """

        # Read JSON config file
        with open(self.config_file_path, 'r') as file:
            data = json.load(file)

        base_link = data['base_link']
        link_mods = data['link_mods']
        spec_mods = data['spec_mods']

        # Generate initial links (without special mods like area, price, commercial, etc.)
        self.feat_links = [base_link + link_mod for link_mod in link_mods]
        
        # Iterate over all the spec_mods -> e.g. start with area [unirii, centru etc.]
        for recur, apply_to_dict in spec_mods.items():
            links_lv2 = []
            leftover_yet_relevant_links = []

            for link in self.feat_links:
                # Apply global mods

                for mod in apply_to_dict.get("apply_to_all", []):
                    links_lv2.append(link + recur + mod)

                # Apply specific mods
                for link_mod, mods in apply_to_dict.items():
                    if link_mod != "apply_to_all" and link_mod in link:
                        for mod in mods:
                            links_lv2.append(link + recur + mod)

            
            # if one of the link mods is not targeted in a spec mod at all, it will not be added to links_lv2
            # in that case we need to add it to leftover_yet_relevant_links
            for feat_link in self.feat_links:
                if not any(x for x in links_lv2 if feat_link in x):
                    leftover_yet_relevant_links.append(feat_link)

            self.feat_links = links_lv2 + leftover_yet_relevant_links

        self.feat_links = [link.replace("/&","/?") for link in self.feat_links]
        
        return self.feat_links



    def scrape_and_save_search_sources(self) -> list[str]:

        """
        This function scrapes the page sources from the links generated from the config file.

        :param feat_links: List of links to scrape.
        :param sleeper: Time to sleep between requests.
        :return: List of paths to folders that contain the page sources.

        """

        # save ymdh to a variable
        ymdh = time.strftime("%Y-%m-%d-%H")

        # make a subfolder with this ymdh variable as name
        output_folder = os.path.join(self.config_folder_path, ymdh)
        try:
            os.makedirs(output_folder)
        except FileExistsError:
            print(
                f"\n --- Error: folder already exists. This means that the this particular config" 
                " has already been run in the last hour. \n - If "
                "you want to run it again, please wait until the next hour. Be gentle to the server. \n"
            )

            if not self.testing:
                return
            print('---> WE ARE TESTING, so we will continue...')
    
        self.current_config_folder_path = output_folder


        def save_page_source(feat_url:str, sleeper:int) -> str:

            feat_mods = feat_url.replace("area=","").replace("commercial=","commercial-").replace("?","")
            
            feat_mods = feat_mods.replace("//","/").split('/')[2:]
            feat_mods = '-'.join(feat_mods)

            # after reaching the final page for a feat link, we are sent back to the 1st page,
            # so we need to check if we are on the 1st page again, if so, break the loop
            reloop_breaker = 0

            page_counter = 2 # we start from pag=2, since page 1 does not contain "pag=1" 
            
            # part_mode is used when we have more than 25 pages for a given Feature
            part_mode = 0
            part_counter = 1

            print_page_counter = 1 # only used for printing

            # Add the path to the geckodriver executable to the system's PATH environment variable
            #os.environ['PATH'] += os.pathsep + '/path/to/geckodriver'

            # Set up the Firefox driver
            all_page_sources = ""
            options = Options()
            options.add_argument("--headless")
            if self.headless == True:
                driver = webdriver.Firefox(options=options)
            else: 
                driver = webdriver.Firefox()

            print(f'Checking pages...')
            while True:
                
                
                driver.get(feat_url)
                page_source = driver.page_source
            
                # wait for the page to load, be gentle to the server
                time.sleep(sleeper)

                # check driver.page_source and make an exception if it is empty
                if page_source == "":
                    print(f'Error: Failed to retrieve page {feat_url}. Status code: {driver.page_source}')
                    print(f'Failed attempt. Please delete the folder {output_folder} and try again.')
                    
                    driver.quit()
                    return
                    
                    
                elif "Nu am găsit ceea ce cauți." in page_source:
                    print("--> No results found. Moving on... ")
                    # we may wanna ad some token to the page source to indicate that there are no results in scrape folder

                    driver.quit()
                    return 
                
                else:
                    print(f' -- > Page {print_page_counter} retrieved')
                    
                
                # the 1st url does not have a page number
                # we are sent back to the 1st page after the last page is reached
                # so we need to check if we are on the 1st page again, if so, break the loop

                if "pag=" not in driver.current_url:
                    reloop_breaker += 1
                    feat_url = feat_url + f'&pag={page_counter}'

                    if reloop_breaker > 1:  

                        # save page source to a file
                        if part_mode == 1:
                            #there is a small bug here, i.e. output folder gets 2x featmods - fixed
                            output_path = output_path.split(feat_mods)[0]
                            output_path = os.path.join(output_folder, f'{feat_mods}-part{part_counter}.html')
                        else:
                            output_path = os.path.join(output_folder, f'{feat_mods}.html')

                        with open(output_path, 'w') as f:
                            f.write(all_page_sources)

                        print(
                            f"\n\n--> Page-Counter-Reloop detected !!!\n" 
                              "--> i.e. No more listings found for this Feature\n" 
                              "--> Saving source file. Moving on... "
                              )
                        break
                
                else: 
                    # prepare the next page url
                    feat_url = feat_url.split('&pag')[0] + f'&pag={page_counter}'

                # save page source to all page sources
                all_page_sources += page_source

                if page_counter >= 25:
                    part_mode = 1

                if part_mode == 1 and page_counter % 25 == 0:

                    output_path = os.path.join(output_folder, f'{feat_mods}-part{part_counter}.html')
                    part_counter += 1
                
                    # save page source to a file
                    with open(output_path, 'w') as f:
                        f.write(all_page_sources)
                    
                    all_page_sources = ""
                    
                page_counter += 1
                print_page_counter += 1


            driver.quit()
            return output_path
        
        feat_links_len = len(self.feat_links)
        feat_link_counter = 1
        

        for feat_link in self.feat_links:
            
            print(f" \n\n -----> Processing feature URL {feat_link_counter}/{feat_links_len}\n" 
                  f"Link : {feat_link}\n\n")
            
            # save page source to a file and append the path to self.page_source_paths
            page_source_path = save_page_source(feat_link,sleeper=self.sleeper)

            if page_source_path != None:
                self.page_source_paths.append(page_source_path)
            
            print(f' -----> Finished processing {feat_link}\n'+"-"*50)
            
            feat_link_counter += 1

        return self.page_source_paths
        

    def get_links_from_html_folder(self) -> dict():
        
        """
        This function scrapes the links from the page sources.

        :param page_source_paths: List of paths to folders that contain the page sources.
        :return: Dictionary with links as values and html filenames (slightly modified) as keys.
        """

        # self.page_source_paths is a list of paths to folders that contain the page sources
        # this is used to generate the .json link file
        html_files = self.page_source_paths

        def scrape_links_from_page_source(source_file):
            # Read the HTML content from a file
                        
            with open(source_file, 'r') as file:
                html_content = file.read()
        
            # Parse the HTML content
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find all li tags with data-adid attribute
            li_tags = soup.find_all('li', attrs={'data-adid': True})

            # For each li tag, find the a tag within it and get the href attribute
            urls = []

            for li in li_tags:
                a_tag = li.find('a')
                if a_tag:
                    url = a_tag.get('href')
                    urls.append(url)

            return urls

        print(f' \n --- Getting links from html files which contained results --- \n')
        source_len = len(html_files)
        source_count = 1

        for file in html_files:
            links = scrape_links_from_page_source(file)
            filename = file.split('/')[-1].replace('.html', '')  # Get filename without extension as key
            self.link_dict[filename] = links
            print(f" ---> {source_count}/{source_len} --- {len(links)} links found")
            source_count += 1
        
        # Remove duplicates
        for filename, links in self.link_dict.items():
            self.link_dict[filename] = list(set(links))

        # save all_links to json
        all_links_json_file_name = self.current_config_folder_path+".json"

        if all_links_json_file_name != "":
            with open(all_links_json_file_name, 'w') as f:
                json.dump(self.link_dict, f, indent=4)

        else:
            print("(Possible) Error: Empty output-json path Please check the code.")
            
        return self.link_dict