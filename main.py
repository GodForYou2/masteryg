# .so ဖိုင်ထဲမှ RuijieBypass class ကို လှမ်းခေါ်ခြင်း
from yourgod import RuijieBypass

if __name__ == "__main__":
    # Class ကို Object ဆောက်သည် (Object ဆောက်တာနဲ့ လိုင်စင်က အော်တိုစစ်မှာပါ)
    app = RuijieBypass()
    
    # app.run_menu() မသုံးတော့ဘဲ တိုက်ရိုက် Run ခိုင်းခြင်း
    try:
        # ကျွန်တော်ပေးထားတဲ့ ကုဒ်အသစ် ဖြစ်နေရင် start_process() က Banner ရော Login ရော တန်းမောင်းပေးပါတယ်
        app.start_process()
    except AttributeError:
        # တကယ်လို့ .so ဖိုင်က ကုဒ်အဟောင်း (Updated မဖြစ်သေးတဲ့ ဖိုင်) ဖြစ်နေသေးရင် 
        # အောက်က မူရင်း function တွေကို တိုက်ရိုက် ဆွဲခေါ်ပြီး ခိုင်းစေပါမယ်
        app.print_banner()
        app.do_login()
