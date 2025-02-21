# This file can be empty 

from . import server

def main():
    server.main()
    
if __name__ == "__main__":
    main()


# Optionally expose other important items at package level
__all__ = ["main", "server"]
