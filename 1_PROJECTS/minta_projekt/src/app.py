"""Minta alkalmazás váz."""
def hello(name: str = "világ") -> str:
    return f"Szia, {name}!"
if __name__ == "__main__":
    print(hello())
