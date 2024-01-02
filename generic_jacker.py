
from pprint import pprint
import sys, os, glob

from FeatPageScraper import FeatPageScraper
from LinkHandler import LinkHandler


from ItemSaver import ItemSaver

# delete failed runs

def check_cli_args(config_file_names) -> list:
    """
    Check command line arguments for configuration file names.

    If no arguments are provided, it will search for all .json files in the 'search_configs' directory.

    :param config_file_names: List of configuration file names.
    :return: List of configuration file paths.
    :raises FileNotFoundError: If a provided file name does not exist.
    """

    if not config_file_names:
        config_file_names = glob.glob(os.path.join("search_configs", "*.json"))
        
        if not config_file_names:
            raise FileNotFoundError(
                "\nNo configuration files found. Please configurations is .json format "
                "to the 'search_configs' directory."
            )
    else:
        
        config_file_names = [os.path.join("search_configs", filename) for filename in config_file_names]
        for file in config_file_names:
            if not os.path.isfile(file):
                raise FileNotFoundError(
                    f"\nFile {file} not found. Please check the name of the "
                    "config file. The file has to be formatted as a .json file. "
                    "Include only the filename, not the path. The path is assumed "
                    "to be 'search_configs'."
                )
    
    print(f"\n Config file path(s) input: {config_file_names} \n")

    return config_file_names


def main():
    try:

        flag = sys.argv[1]
        config_files = check_cli_args(sys.argv[2:])
   
    except FileNotFoundError as e:
        print(str(e))
   
        print(
            f" \n---> Usage: generic_jacker.py [flag][file_1][file_2][...] for selecting config_files"
            " from 'search_configs' folder OR generic_jacker.py [flag] to select ALL configs from"
            " the folder."
            )
        sys.exit(1)

    if flag == "-run":

        for config in config_files:
        
            print(f"\n------- > Processing search config {config} .....")
            
            link_handler = LinkHandler(config)
            link_handler.clean_failed_runs()
            
            feat_page_scraper = FeatPageScraper(config)


            feat_page_scraper.generate_links_from_config_json()
            feat_page_scraper.scrape_and_save_search_sources()
            feat_page_scraper.get_links_from_html_folder()

    else:

        for config in config_files:
            
            link_handler = LinkHandler(config)
            
            if flag == "-t":
                link_handler.timetable()
            
            elif flag == "-ca":
                to_print = link_handler.get_last_link_json()
                link_handler.print_links(to_print)

            elif flag == "-cd":
                to_print = link_handler.get_current_diff()
                link_handler.print_links(to_print)

            elif flag == "-cao":
                to_open = link_handler.get_last_link_json()
                link_handler.open_links(to_open)
                
            elif flag == "-cdo":
                to_open = link_handler.get_current_diff()
                link_handler.open_links(to_open)
                
            elif flag == "-s":
                to_print = link_handler.get_specific_json()
                link_handler.print_links(to_print)

            else:
                print(
                    f"Invalid flag. Use: \n -t for timetable \n -ca for current all \n -cd for current"
                    " diff \n -cao for current all open \n -cdo for current diff open. \n -s for specific"
                    " json file, but this is not recommended.\n"
                    )
                sys.exit(1)
        
if __name__ == "__main__":
    main()


    """
        link_handler = LinkHandler(config_source)

        #pprint(link_dict)
        #pprint(feat_links)

        item_saver = ItemSaver(config_source)
        print("\n Number of in json files: ",len(item_saver.get_item_links_in_json_files()))
        print(" Number of items already saved : ",len(item_saver.get_item_links_already_saved()))
        print(" --> Items left: ")
        items_to_be_saved = item_saver.get_item_links_to_be_saved()
        pprint(items_to_be_saved[:10])
        print("...")

        item_saver.save_item_html_files()
        
        if "caut_chirie_minimal" in config_source:
            
            link_handler.open_last_link_diffz()
            """
    