# Smart Grocery user guide

## Start on macOS

Open the repository root in VS Code. For manual terminal commands below, first enter `cd ROI`. Select Terminal > Run Task > Grocery: Run desktop app. To launch from the integrated terminal, enter `python3 gui.py`. Python 3.10 or later with Tkinter is required. The current Mac has Python 3.15 and Tk 9.

The first run provides five sample products. Milk has product ID 2, a unit price of RM 7.50 and 15 units. The application reads inventory.json from the folder where you start it. Keep that working folder consistent when switching between the desktop and console.

## Register a product

Click Add Product, or press Command-N. Enter an unused ID containing one to six letters or digits, a name of up to 24 characters, a price and opening stock. For a reproducible example, enter A01, Apples, 2.35 and 6. Click Save Product. The application saves the product and stock together.

Prices accept up to two decimal places and must be between RM 0.01 and RM 99,999. Opening stock accepts zero or a positive whole number. An invalid entry shows a message in the form. Correct it and save again.

## Build and edit a sale

Use Search products, or Command-F, to find Milk. Select the row, enter 2 in Quantity and click Add to Cart. The current sale should show two units with an amount of RM 15.00. Repeated additions combine quantities.

Select a cart row and click Remove Item to remove that product. Clear Cart removes all items from the current sale. To change a quantity, remove the row and add the desired quantity again.

## Complete the sale

Click Checkout and confirm the RM 15.00 purchase. The cart clears and milk stock becomes 13. A confirmation message reports that stock was saved. Cancelling the confirmation retains the cart and stock.

If a file cannot be saved, the desktop displays an error and retains the cart and stock. Resolve the file or disk issue and retry. Close and reopen the app to verify the saved stock. Closing with a cart asks whether to discard that uncompleted sale.

## Console demonstration

Run `python3 main.py`, or select Grocery: Run Assignment 2 in the task menu. The options cover viewing stock, registration, adding to the cart, viewing the cart, checkout, clearing the cart and exit. For the sample milk sale enter 3, 2, 2, then 5 and y. Option 1 shows the revised stock and 0 exits.

Use `python3 main.py --data demo-inventory.json` to keep a demonstration separate from another inventory file. Reuse the same option on restart to verify persistence.

## Tests and evidence

Run `python3 -m unittest discover -s tests -v`, or select Grocery: Run all tests. The 14 test methods cover normal purchases, invalid entries, cancellation, persistence, future expiry workflows, desktop save failures and damaged saved records. Tests use temporary inventory files.

The evidence folder contains observed console output, restart output and the test result log. These are captured program transcripts. Desktop transaction tests use mocked dialogs. Complete the visual walkthrough below on the Mac to add screenshots to the submission.

## Visual demonstration checklist

Capture the following views during one demonstration, with readable text and the full relevant window. Add captions explaining the entered values and observed result.

1. Products showing the initial milk price and stock.
2. The Add Product form filled with A01, Apples, RM 2.35 and six units.
3. The saved Apples row in the catalogue.
4. Two milk units in the cart with a total of RM 15.00.
5. An invalid or excessive quantity and its feedback message.
6. The completed sale with 13 milk units and an empty cart.
7. The same stock after restarting the app.

Record the date, tester and any unexpected behaviour. GUI screenshot evidence is pending.

## Data and limitations

Use one running application per inventory file. The current whole-file storage is intended for a single user. It stores product, batch and discard records. Receipts and sales history are future enhancements.

The existing expiry and waste prototype uses `python3 main.py --final-project`. It adds stock receiving, expiry checks and waste reports. Verify the dates of carried-over stock before selling it in that mode. The desktop applies expiry eligibility when it opens a dated inventory.

If the saved file is damaged, startup reports an error. Restore a known-good copy or correct the affected records. Invalid saved data is rejected before a transaction begins.
