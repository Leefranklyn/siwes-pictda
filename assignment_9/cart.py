"""
This program is a simple Shopping Cart system that uses a list
to store and manage products. Users can add products, remove
products, view the cart, and count the total number of products.
"""

products = []


def add_product():
    """Add a product to the shopping cart."""
    product = input("Enter Product Name: ").strip()

    if product:
        products.append(product)
        print("Product Added Successfully")
    else:
        print("Product name cannot be empty.")


def remove_product():
    """Remove a selected product from the shopping cart."""
    if not products:
        print("There are no products in the cart.")
        return

    view_cart()

    try:
        index = int(input("Enter the index of the product to remove: "))

        if 0 <= index < len(products):
            removed_product = products.pop(index)
            print(f"{removed_product} removed successfully.")
        else:
            print("Invalid index.")

    except ValueError:
        print("Please enter a valid number.")


def view_cart():
    """Display all products currently in the shopping cart."""
    if not products:
        print("The shopping cart is empty.")
        return

    print("\n===== Shopping Cart =====")

    for index, product in enumerate(products):
        print(f"{index}. {product}")


def total_products():
    """Display the total number of products in the shopping cart."""
    print(f"Total Products: {len(products)}")


def main():
    """Run the main shopping cart menu and handle user selections."""
    while True:
        print("\n===== Shopping Cart =====")
        print("1. Add Product")
        print("2. Remove Product")
        print("3. View Cart")
        print("4. Total Products")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            add_product()

        elif choice == "2":
            remove_product()

        elif choice == "3":
            view_cart()

        elif choice == "4":
            total_products()

        elif choice == "5":
            print("Exiting Shopping Cart...")
            break

        else:
            print("Invalid option. Please select 1-5.")


main()
