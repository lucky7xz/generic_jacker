import os, glob, json, time, shutil
import webbrowser

class LinkHandler:

    def __init__(self, config_file_path: str):

        """
        This class is used to handle the link dictionaries scraped from the web.

        functions:

        timetable() - counts the number of links in each .json file, but also the number of links
        that are not in the previous .json file.

        """
        
        self.config_file_path = config_file_path
        
        self.config_folder_name = os.path.basename(config_file_path).replace('.json','')
        self.config_folder_path = os.path.join("page_source_folder",self.config_folder_name)

        self.all_json_files = glob.glob(self.config_folder_path + '/*.json')
        self.all_json_files.sort(key=os.path.getmtime)

        self.diff_dict = {}


    def timetable(self) -> dict():
        '''
        Within the page source folder there are multiple .json files that are formatted like this:
        yyyy-mm-dd-hh - each contains a dictionary with features (diffrent # of rooms etc.) as keys 
        and a list of links as coresponding value.

        This function countes the number of links in each .json file, but also the number of links 
        that are not in the previous .json file.
        '''
        print("\n\n--- Counting links and computing the diffs from all json files ---\n")

        # initialize previous links as empty
        prev_links = []
        for json_file in self.all_json_files:
            
            with open(json_file, 'r') as f:
                current_links_dict = json.load(f)
                # Flatten list of lists, some semantic loss here.
                current_links = [link for links in current_links_dict.values() for link in links]  
                
                diff_links = list(set(current_links) - set(prev_links))
                print(f" {json_file}  :  {len(current_links)} total links."
                      f"({len(diff_links)} new links compared to the previous file.)")

                self.diff_dict[json_file] = diff_links

                # set current links to previous links for the next iteration
                prev_links = current_links
        
        print("---> Done computing the diffs from all json files ---\n")

        return self.diff_dict


    def open_links(self, link_dict: dict, opening_delay: int = 1) -> None:
    
        total_link_count = 0
        to_open = []
        for filename, links in link_dict.items():
            total_link_count += len(links)
            to_open.extend(links)

        print("\n Total Links to be opened: ",total_link_count)
        print("Opening last scraped links in 3..2..1... ")

        time.sleep(3)
    
        for i in range(len(to_open)):
            webbrowser.open(to_open[i])
            time.sleep(opening_delay)
        
        
        # count the number of links in the last json file
            
    def print_links(self, link_dict: dict):
        
        counter = 1
        for key, value in link_dict.items():
            print(f"\nFeature : {key}\n\n")

            if len(value) == 0:
                print("---> No new links.")

            else:
                for link in value:
                    print(f"{counter} : {link}")
                    counter += 1
            print("*"*50)

        print(f"\n ---> Total number of new links: {counter-1}\n\n")

    
    def clean_failed_runs(self)-> None:
        """
        This function will be triggered before the run of the scraper. It will delete
        all folders with yyyy-mm-dd-hh format that do not have a corresponding .json file.

        This ensures more consistent data, since the json is created at the very end of a scrape run,
        i.e. if the run fails for any reason, the json file will not be created.
        """

        json_files = [os.path.basename(file) for file in self.all_json_files]
        path = os.path.join("page_source_folder", self.config_folder_name)

        list_of_folders = os.listdir(path)
        
        if "item_html_files" in list_of_folders:
            list_of_folders.remove("item_html_files")


        list_of_folders = list(set(list_of_folders) - set(json_files) 
                               - set([json_file.replace(".json","") for json_file in json_files]))
        
        
        print("Let's clean up first! \nList of failed-run folders names for this: ",list_of_folders)

        # confirm deletion, just in case other folders are in the same directory

        confirm = input("Are you sure you want to delete these folders? (y/n) - ")

        if confirm == "y":
            for folder in list_of_folders:
                folder_path = os.path.join(path, folder)
                
                # directory will probably not be empty, so we'll use shutil.rmtree
                shutil.rmtree(folder_path)
        else:
            print("No folders deleted.")


    def get_specific_json(self)-> json:

        date = input("Enter date in format 'yyyy-mm-dd-hh' - ")

        json_file = os.path.join(self.config_folder_path, date + ".json")

        if not os.path.isfile(json_file):
            raise FileNotFoundError(
                f"\nFile {json_file} not found. Please check the name of the "
                "config file. The file has to be formatted as a .json file. "
                "Include only the filename, not the path. The path is assumed "
                "to be 'page_source_folder'."
            )
        
        with open(json_file, 'r') as f:
            links_dict = json.load(f)
        
        return links_dict
    
    def get_current_diff(self)-> dict:
        
        except_last = self.all_json_files[:-1]
        last = self.all_json_files[-1]

        new_dict = {}

        all_prev_links = []

        for json_file in except_last:
            with open(json_file, 'r') as f:
                current_links_dict = json.load(f)
        
            current_links = [link for links in current_links_dict.values() for link in links]
            all_prev_links.extend(current_links)

        
        with open(last, 'r') as f:
            last_links_dict = json.load(f)
        
        # we'll use pop to prevent the semnatic loss of flattening the list of lists
            
        for key, value in last_links_dict.items():
            new_dict[key] = list(set(value) - set(all_prev_links))

        return new_dict
    

    def get_last_link_json(self) -> dict:

        last_json = self.all_json_files[-1]

        with open(last_json, 'r') as f:
            last_links_dict = json.load(f)

        return last_links_dict
    



