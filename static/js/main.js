function fetchItemName() {
    const code = document.getElementById('item_code').value;
    if (!code) return;
    fetch('/api/item/' + code)
        .then(response => response.json())
        .then(data => {
            if (data.item_name) {
                document.getElementById('item_name').value = data.item_name;
                if (data.lot_number) document.getElementById('lot_number').value = data.lot_number;
            } else {
                alert('商品が見つかりませんでした');
            }
        });
}

function fetchItemCode() {
    const name = document.getElementById('item_name').value;
    if (!name) return;
    fetch('/api/code/' + name)
        .then(response => response.json())
        .then(data => {
            if (data.item_code) {
                document.getElementById('item_code').value = data.item_code;
                if (data.lot_number) document.getElementById('lot_number').value = data.lot_number;
            } else {
                alert('商品が見つかりませんでした');
            }
        });
}

function fetchItemByLot() {
    const lot = document.getElementById('lot_number').value;
    if (!lot) return;
    fetch('/api/lot/' + lot)
        .then(response => response.json())
        .then(data => {
            if (data.item_code) {
                document.getElementById('item_code').value = data.item_code;
                document.getElementById('item_name').value = data.item_name;
            } else {
                alert('商品が見つかりませんでした');
            }
        });
}
