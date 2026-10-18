import flet as ft
import requests
import pyperclip
import ssl
import os

# این دو خط باعث می‌شوند پایتون تایید SSL را نادیده بگیرد
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['CURL_CA_BUNDLE'] = ''

# ⚠️ حتماً لینک جدید را از گوگل اسکریپت (بعد از Deploy) اینجا قرار دهید
API_URL = "https://script.google.com/macros/s/AKfycbwVkcIn12GJ-8GQTVa-eOD8ijhU6zTbPi3qlCGCKj-Vxsu0Wksy7QUg3nzTFM442HQ52g/exec"

class DinoSellerApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Dino Shop - Seller Panel"
        self.page.rtl = True
        self.page.theme_mode = ft.ThemeMode.DARK
        
        self.orders_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        self.setup_ui()
        self.load_orders()

    def setup_ui(self):
        """تنظیم ساختار اصلی صفحه"""
        self.page.appbar = ft.AppBar(
            title=ft.Text("پنل مدیریت فروشنده 🛠️"),
            center_title=True,
            bgcolor=ft.colors.BLUE_GREY_900,
            actions=[
                ft.IconButton(
                    icon=ft.icons.ADD_BOX, 
                    tooltip="افزودن محصول جدید",
                    on_click=lambda _: self.show_add_product_dialog()
                ),
                ft.IconButton(
                    icon=ft.icons.REFRESH, 
                    tooltip="بروزرسانی لیست",
                    on_click=lambda _: self.load_orders()
                ),
            ]
        )
        
        refresh_btn = ft.FloatingActionButton(
            icon=ft.icons.REFRESH,
            on_click=lambda _: self.load_orders(),
            bgcolor=ft.colors.BLUE
        )

        self.page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("سفارشات دریافتی جدید:", size=22, weight="bold", color=ft.colors.AMBER_ACCENT),
                    ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                    self.orders_list
                ], expand=True),
                padding=20
            ),
            refresh_btn
        )

    def show_snack_bar_custom(self, message):
        """نمایش پیام اعلان"""
        self.page.show_snack_bar(ft.SnackBar(ft.Text(message)))

    def copy_to_clipboard(self, text):
        """کپی کردن شماره در کلیپ‌بورد با رفع خطای TypeError"""
        # تبدیل به رشته برای جلوگیری از خطای 'int' object is not iterable
        str_text = str(text)
        # پاکسازی شماره از کاراکترهای غیر عددی
        clean_text = "".join(filter(str.isdigit, str_text))
        
        pyperclip.copy(clean_text)
        self.show_snack_bar_custom(f"شماره کپی شد: {clean_text}")

    def load_orders(self):
        """دریافت سفارشات از گوگل اسکریپت"""
        self.orders_list.controls.clear()
        
        self.orders_list.controls.append(
            ft.Container(
                content=ft.ProgressBar(width=400, color=ft.colors.AMBER),
                alignment=ft.alignment.center,
                padding=20
            )
        )
        self.page.update()
        
        try:
            response = requests.get(f"{API_URL}?action=getOrders")
            
            if response.status_code == 200:
                orders = response.json()
                self.orders_list.controls.clear()
                
                if not orders:
                    self.orders_list.controls.append(
                        ft.Text("هیچ سفارش جدیدی وجود ندارد. 🎉", size=16, text_align="center")
                    )
                else:
                    for order in orders:
                        self.orders_list.controls.append(self.create_order_card(order))
            else:
                self.orders_list.controls.append(ft.Text(f"خطا در دریافت اطلاعات: {response.status_code}"))
        except Exception as e:
            self.orders_list.controls.append(ft.Text(f"خطای شبکه: {e}"))
        
        self.page.update()

    def create_order_card(self, order):
        """ساخت ظاهر هر کارت سفارش با دکمه کپی شماره"""
        return ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.SHOPPING_BAG, color=ft.colors.AMBER),
                        title=ft.Text(f"مشتری: {order['customer_name']}", weight="bold"),
                        subtitle=ft.Text(f"مبلغ: {order['total_price']:,} تومان", color=ft.colors.AMBER_200),
                    ),
                    ft.Text(f"محصولات: {order['items']}", size=13, color=ft.colors.GREY_400),
                    ft.Divider(height=10),
                    ft.Row(
                        [
                            ft.Text(f"📞 {order['phone']}", size=15, weight="w500"),
                            ft.ElevatedButton(
                                content=ft.Row([
                                    ft.Icon(ft.icons.COPY, size=16),
                                    ft.Text("کپی شماره")
                                ], tight=True),
                                icon=None,
                                bgcolor=ft.colors.BLUE_GREY_700,
                                color=ft.colors.WHITE,
                                on_click=lambda _, p=order['phone']: self.copy_to_clipboard(p)
                            )
                        ], 
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    )
                ])
            )
        )

    def show_add_product_dialog(self):
        """فرم افزودن محصول جدید"""
        id_input = ft.TextField(label="کد محصول (ID)", width=350)
        name_input = ft.TextField(label="نام محصول", width=350)
        price_input = ft.TextField(label="قیمت (تومان)", width=350, keyboard_type=ft.KeyboardType.NUMBER)
        desc_input = ft.TextField(label="توضیحات", width=350, multiline=True, min_lines=2)
        img_input = ft.TextField(label="لینک مستقیم عکس (URL)", width=350)
        dim_input = ft.TextField(label="ابعاد (مثلاً ۲۰*۳۰)", width=350)

        def submit_new_product(e):
            if not name_input.value or not price_input.value:
                self.show_snack_bar_custom("لطفاً نام و قیمت را وارد کنید!")
                return

            payload = {
                "action": "addProduct",
                "id": id_input.value,
                "name": name_input.value,
                "price": price_input.value,
                "description": desc_input.value,
                "image_url": img_input.value,
                "dimensions": dim_input.value
            }

            try:
                res = requests.post(API_URL, json=payload)
                if res.status_code == 200:
                    self.show_snack_bar_custom("✅ محصول با موفقیت ثبت شد!")
                    self.page.close(dlg)
                    self.load_orders()
                else:
                    self.show_snack_bar_custom("خطا در ثبت محصول")
            except Exception as ex:
                self.show_snack_bar_custom(f"خطای شبکه: {ex}")

        dlg = ft.AlertDialog(
            title=ft.Text("افزودن محصول جدید 🍰"),
            content=ft.Column([
                id_input, name_input, price_input, desc_input, img_input, dim_input
            ], tight=True, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("لغو", on_click=lambda _: self.page.close(dlg)),
                ft.ElevatedButton("ذخیره در لیست", on_click=submit_new_product, bgcolor=ft.colors.AMBER_700, color=ft.colors.WHITE)
            ]
        )
        self.page.open(dlg)

def main(page: ft.Page):
    DinoSellerApp(page)

if __name__ == "__main__":
    ft.app(target=main)
