import csv
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Arguments for Sparta Program")
    parser.add_argument("inputFile", type=str, help="Path to input file", required=True)
    
    print(inputFile)