# -*- coding: utf-8 -*-


import os
import sys
import logging
import argparse,  traceback

#modul rekayasa waktu
from datetime import datetime, timedelta,timezone

# pendownload halaman web, membaca halaman tanpa download, cek update realtime
import requests

#modul speed up pandas
from functools import lru_cache

# tes memori formula
from sys import getsizeof 

#testing/produksi?
testing =  True  #or False


def send_mail(body):

	# modul kirim email by google
    from smtplib import SMTP
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    message = MIMEMultipart()
    message['Subject'] = 'Potensi selisih order book'
    message['From'] = 'ringkasan.akun@gmail.com'
    receiver_email= ['venoajie@gmail.com'] if testing == True else ['venoajie@gmail.com','gerykurniawan02@gmail.com','vinaoctaviana@gmail.com','lugie.y@gmail.com']
    emaillist = [elem.strip().split(',') for elem in receiver_email]

    body_content = body
    message.attach(MIMEText(body_content, "html"))
    msg_body = message.as_string()

    server = SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(message['From'], 'ceger844579*')
    server.sendmail(message['From'], emaillist, msg_body)
    server.quit()

def telegram_bot_sendtext(bot_message):

	bot_token   = '1035682714:AAGea_Lk2ZH3X6BHJt3xAudQDSn5RHwYQJM'
	bot_chatID  = '148190671'
	send_text   = 'https://api.telegram.org/bot' + bot_token + (
								'/sendMessage?chat_id=') + bot_chatID + (
							'&parse_mode=HTML&text=') + bot_message

	response    = requests.get(send_text)

	return response.json()

#TODO: Logger

def get_logger( name, log_level ):

	'''
		Logger untuk informasi debug

		 Returns:           
			informasi debug
	'''

	formatter = logging.Formatter( fmt = '%(asctime)s - %(levelname)s - %(message)s' )
	handler = logging.StreamHandler()
	handler.setFormatter( formatter )
	logger = logging.getLogger( name )
	logger.setLevel( log_level )
	logger.addHandler( handler )
#	time_now        =	time.mktime(NOW_TIME.timetuple())

	return logger


#TODO: restart
	"""
	restart program

	"""
def restart_program():

	python = sys.executable
	os.execl(python, python, * sys.argv)


def cek_hari_kerja () : #!--> integer

    '''
        Mengecek apakah sekarang hari kerja bursa
        +  #mendapatkan waktu UTC saat ini 
        +  Mengubah waktu UTC ke Jakarta
                        
        Returns:           
            hari kerja: 1-5, libur: 6-7

    '''
    return int(((datetime.today()) + (timedelta(hours = 7))).strftime('%w'))

waktu_kerja_jakarta=cek_hari_kerja () 

 #Jangan proses kalau sabtu/minggu
if testing == False and waktu_kerja_jakarta > 5:
    my_message=  'Sabtu/Minggu, no data'
    (telegram_bot_sendtext(my_message)	    )
#! bagaimana behaviour di linux?
    x=5/0

#* update status melalui telegram
(telegram_bot_sendtext((f"Mulai penarikan data, hari kerja {waktu_kerja_jakarta}, testing {testing}"))	    ) 


#class OrderBook(object):  

 #   def __init__(self, monitor=True, output=True):
    
  #      self.logger = None        
   #     self.monitor = monitor
    #    self.output = output or monitor

def  step_fr_buy_to_sell (laba,harga) : #!--> integer

    '''
        Menghitung banyaknya jarak yang diperlukan sejak beli sampai dengan jual saham
        dengan cara membagi laba dengan fraksi saham/Tick
                        
        Returns:           
            jarak dalam integer

    '''
    
    fraksi = 0

    if harga < 200:
        fraksi = 1
        
    elif harga < 500:
        fraksi = 2
        
    elif harga < 2000:
        fraksi = 5
        
    elif harga < 5000:
        fraksi = 10
        
    else:
        fraksi = 25

    jarak= laba / fraksi

    return int(jarak)

@lru_cache(maxsize=None)
def  emiten_saham () : #!--> list

    '''
        Menarik data emiten dan menyaringnya dengan kriteria tertentu sebelum diolah lebih lanjut
                        
        Returns:           
            Nama2 emiten saham terpilih

    '''

    # download saham dan harga saham
    import data_emiten
    
    #* Menarik seluruh saham beserta atribut harganya dari daftar 
    populasi=data_emiten.data_emiten()
    
    #* Filter saham 1: harga 50 dikeluarkan
    emiten_harga_gocap=[ o['saham'] for o in[o for o in populasi if int(o['mid_prc']) < 60]] 
 
    #* Hanya nama saham saja
    populasi= [ o['saham'] for o in[o for o in populasi ]]

    #* Filter saham 2: harga 50 dikeluarkan + emiten bermasalah (ditambahkan secara manual)
    emiten_bermasalah=list(['KPAL','BLTA'] + emiten_harga_gocap)

    #* Untuk kepentingan testing, abaikan
    emiten_code_bumn=['WEHA','INPC','ABBA','KPAL','BLTA']#,'BMRI','JSMR','PGAS','ANTM','KRAS','GIAA','IPCC','WSKT','ANTM']
#https://stackoverflow.com/questions/50665276/appending-dataframe-data-to-a-json-file-without-deleting-previous-content

    #* Emiten saham terseleksi (populasi minus saham bermasalah)
    emiten_saham = emiten_code_bumn if testing == True else [o for o in populasi if o not in emiten_bermasalah]

    return (emiten_saham)

emiten_saham = emiten_saham()

@lru_cache(maxsize=None)
def ekstraksi_data():  #!--> list

    '''
        Mengekstrak data order book dari website IPOT 
        
        + Orderbook yang sudah didapat kemudian diseleksi berdasarkan kriteria seperti potensi laba, jarak beli ke jual, harga saham, dst
                
        Returns:           
            list saham yang punya potensi dengan usulan harga beli, jual dan jarak
    '''

    # modul perekayasa data
    import pandas as pd

    #! menyiapkan penampungan untuk hasil saham terplih
    result = []	

    #! untuk setiap emiten terpilih dari populasi:
    for emiten in emiten_saham:	

        #! endpoint alamat order book IPOT
        print(emiten)
        waktu=datetime.now()
        print(waktu)
        
        end_point = 'https://www.indopremier.com/ipotgo/lp-orderbook.php?ref=tg&code='

        #! Menggabungkan alamat dengan daftar emiten 	
        end_point= (end_point + emiten) 		

        #* Mengolah infomasi saham menggunakan pandas				

        #? Menggunakan 'try/except' untuk membuang saham yang tidak dapat dipakai akibat inkonsistensi data 
        #? di IPOT (M menggantikan '000 000, text/number, spasi, dst)  atau pun adanya saham2 yang bermasalah (saham gocap/suspend)				

        try:

            #* Merapikan data, membuang N/a dan kolom2 yang tidak perlu	
            df = pd.read_html((end_point),na_values=["TOTAL"])
            df_summary = df[0]

            #* Mendapatkan lot saham hari ini			
            lot= ( [ o  for o in[o for o in df_summary[7] ]][0]		)

#TODO: efisiensi: tambah filter berdasarkan lot sehingga tidak perlu diteruskan prosesnya ke 'df'
            
            df = df[1].head(11)		
            df = (pd.DataFrame(df)[:-1]).dropna(how='all', axis='columns')

        #	contoh informasi dari tarikan df_summary, emiten SMGR, 22-12-2020, 10:53:
            #!	    0        1   2     3      4   5    6       7
            #!	0  Prev  12500.0 NaN  Open  12300 NaN  Lot   17310
            #!	1   Chg    -25.0 NaN  High  12700 NaN  Val  21.7 B
            #!	2     %     -0.2 NaN   Low  12300 NaN  Avg   12511

        #	contoh  informasi dari tarikan df[1].head(11), emiten TLKM, 22-12-2020, 9:10:

            #!		BidLot     Bid   Offer  OffLot  
            #!	0     883  3480.0  3490.0    5321       
            #!	1   11140  3470.0  3500.0   18714       
            #!	2   12924  3460.0  3510.0   18865       
            #!	3   22291  3450.0  3520.0   18495       
            #!	4   40204  3440.0  3530.0    3929      
            #!	5   12071  3430.0  3540.0   12188      
            #!	6   12883  3420.0  3550.0   40465        
            #!	7   15595  3410.0  3560.0   15393        
            #!	8   18868  3400.0  3570.0   26113      
            #!	9    2531  3390.0  3580.0   14960       

            #* Menghitung potensi laba di orderbook dengan cara mengofset/mengurangkan lot jual dengan lot beli				
            #* Mengubah format angka ke integer untuk memastikan konsistensi dan menjumlah hasilnya secara kumulatif (menggunakan cumsum)				
            df['offsetting']=(df['OffLot'].astype(int)-df['BidLot'].astype(int)).cumsum()			

            #* Menentukan harga berdasarkan tanda kumulatif (+: bid/-: offer, true= 1, false=0, true/false * harga)				
            df['prc'] = ((df['offsetting'] > 0) * df['Bid'])  	
            df['prc'] = abs(((df['offsetting'] <0) * df['Offer'])  - df['prc'] )
            df['sign'] =  (df['offsetting'] > 0) 	
            df['sign'] =  ((df['offsetting'] < 0) )  	

            print (df)	 #for debug purpose only, abaikan
            print ('df[prc]',df['prc'])	#for debug purpose only, abaikan

        #	contoh olahan tarikan, emiten TLKM, 22-12-2020, 9:10:
        #!			BidLot     Bid   Offer  OffLot  offsetting     prc
            #!	0     883  3480.0  3490.0    5321        4438  3480.0
            #!	1   11140  3470.0  3500.0   18714       12012  3470.0
            #!	2   12924  3460.0  3510.0   18865       17953  3460.0
            #!	3   22291  3450.0  3520.0   18495       14157  3450.0
            #!	4   40204  3440.0  3530.0    3929      -22118  3530.0
            #!	5   12071  3430.0  3540.0   12188      -22001  3540.0
            #!	6   12883  3420.0  3550.0   40465        5581  3420.0
            #!	7   15595  3410.0  3560.0   15393        5379  3410.0
            #!	8   18868  3400.0  3570.0   26113       12624  3400.0
            #!	9    2531  3390.0  3580.0   14960       25053  3390.0

#FIXME:
        #	contoh  tarikan ngaco, emiten FREN, 22-12-2020, 11:21, filter out, tidak bisa diolah lebih lanjut sebelum didecoding masalahnya:
            #!		BidLot   Bid  Offer  OffLot
            #!	0  2.0 M  71.0   72.0  888172
            #!	1  2.4 M  70.0   73.0   1.4 M
            #!	2  1.4 M  69.0   74.0   1.7 M
            #!	3  1.1 M  68.0   75.0   2.0 M
            #!	4  1.5 M  67.0   76.0   1.1 M
            #!	5      0   0.0   77.0   1.0 M
            #!	6      0   0.0   78.0   1.1 M
            #!	7      0   0.0   79.0  939895
            #!	8      0   0.0   80.0   2.1 M
            #!	9      0   0.0   81.0   1.0 M
    

            #* Memisahkan hasil ofset ke dalam list				
            prc_list= [ o  for o in[o for o in df['prc'] ]]
            print ('prc_list A',prc_list)	#for debug purpose only, abaikan

            #* Mendapatkan indikasi jual/beli dengan mengurangkan order book urutan row i dan i-1		
            prc_list=  [prc_list[i] for i in range(0, len(prc_list)) if  prc_list[i - 1] - prc_list[i] < 0 ]
            
            print ('prc_list',prc_list)	#for debug purpose only, abaikan

            #* Mendapatkan harga saham hari sebelumnya			
            harga_pembukaan = int( [ o  for o in[o for o in df_summary[1] ]][0]		)

            #* Mendapatkan best bid			
            best_bid =  max(df['Bid'])	

        #* Memberi nilai untuk semua angka ngaco agar perhitungan selanjutnya tidak error
        except:
            prc_list = []
            df=[]
            print(df)
#			df['offsetting']=[]
#			df['prc']	=[]
            harga_pembukaan  = 0

        #* Menghitung potensi laba Rp/ %, 0 bila price list hanya ada 1/kosong [] dan harga 50
        jual=0 if (len(prc_list) == 1  or prc_list == []) else max (prc_list)
        beli=0 if (len(prc_list) == 1 or prc_list == []) else  min(prc_list)
        laba_rp= 0 if ( jual - beli == 0 or harga_pembukaan  ==50 or prc_list == []) else (( jual - beli )) #Rp
        labaPct=  0 if laba_rp==0 else round(laba_rp/ beli * 100,2) #%

        #* Menghitung jarak penyelesaiann transaksi (laba/fraksi)
        jarakBeliKeJual = 0 if prc_list == [] else step_fr_buy_to_sell ( laba_rp, harga_pembukaan )
        jarakBelikeMid = 0 if prc_list == [] else step_fr_buy_to_sell ( (best_bid-beli), best_bid )

        #* Contoh mengapa jarak beli ke Mid price penting: solusi perlu dioptimalisasi, lebih baik bisa menunjuk langsung ke 490
        #!	BidLot    Bid  Offer  OffLot  offsetting    prc
        #!	0     162  510.0  520.0     545         383  510.0
        #!	1      78  505.0  525.0     888        1193  505.0
        #!	2     614  500.0  530.0    1779        2358  500.0
        #!	3      77  498.0  535.0     374        2655  498.0
        #!	4     261  496.0  540.0       3        2397  496.0
        #!	5     795  494.0  545.0     556        2158  494.0
        #!	6     334  492.0  550.0     689        2513  492.0
        #!	7    4682  490.0  555.0     168       -2001  555.0
        #!	8       0    0.0  560.0     305       -1696  560.0
        #!	9       0    0.0  565.0      92       -1604  565.0
            #! Tanpa menghitung jarak ke midprice, maka 'MBSS mjd layak beliL beli 555.0 jual 565.0 laba 1.8  langkah 2'
            #! padahal 


        #* Menghitung kriteria lanjutan saham layak beli

        #*tes kesehatan order book/ob, dianggap sehat bila minimum ada 100 lot		

        #* tarik populasi orderbook net (bid-sell)		
    

        #* cari jumlah minimum dari populasi order book		
        try:

            ob_oke =[ o  for o in[o for o in df['offsetting'] ]]

        except:

            ob_oke = 0

        ob_oke =0 if ob_oke==0 else  min ((max (ob_oke)) , abs(min(ob_oke)))
        mid_prc= (jual + beli)/2

        #* filter data berdasarkan jarak		
        jarak=4

        layak_beli = True if testing == True else labaPct >1 and jarakBeliKeJual  < jarak and ob_oke  > 100 and jarakBelikeMid < jarak and  harga_pembukaan  != 50

        hasil=(emiten,'layak_beli',layak_beli,'harga_pembukaan ',harga_pembukaan ,'laba',labaPct,jarakBeliKeJual ,ob_oke) #for debug purpose only, abaikan

        #* Menggabungkan saham layak beli ke dalam list
        if layak_beli:

            (telegram_bot_sendtext(f"{emiten} mid_prc {mid_prc}  beli {beli} jual {jual} laba {labaPct}  jarak Beli ke Jual  {jarakBeliKeJual } ")	    ) 

            if testing == False:
                result.append({
                "saham":emiten,
                "mid_prc":mid_prc,
                "beli":beli,
                "jual":jual,
                "laba":labaPct,
                "jarak":jarakBeliKeJual 
            })


            if testing == True:
                result.append({
                "saham":emiten,
                "prev_prc":harga_pembukaan,
                "beli":beli,
                "jual":jual,
                "laba":labaPct,
                "jarak":jarakBeliKeJual 
            })
            import json
            with open('outputfile', 'w') as fout:
                waktu=datetime.now()
                json.dump(result, fout)

    #! Merapikan data: sort & tabel		

    #* sort list berdasarkan jarak
    result  = sorted((result), key=lambda k: k['jarak'])
    
    #* ganti format list ke dataframe
    result  = (pd.DataFrame(result)	)

    #* agar index dimulai dari 1, bukan 0
    result.index += 1 

    print(result) #for debug purpose only, abaikan

    return (result)


def  format_html () : #!--> string

    '''
        Meyiapkan isi dan format email
                        
        Returns:           
            Isi dan format e mail

    '''

    html = """
    <html>
    <head>
    <style> 
    table, th, td {{ border: 1px solid black; border-collapse: collapse; }}
    th, td {{ padding: 5px; }}
    </style>
    </head>
    <body><p>Hi All,</p>

    <p> Tarikan order book saham yang berpotensi laba untuk dicek ulang:  </p>
    <p> Hati-hati dengan delay data + kesalahan formula. Tetap harus menghitung manual/konfirmasi visual sebelum memutuskan transaksi.  </p>
    {table}

    <p> Parameter filter (untuk ditune up): Harga: > 60, Laba: > 1 %', Lot: > 100, Jarak: < 5 </p>
    
    <p>Jadwal penarikan data:<br>
    Pembukaan sesi 1: 09:35 --> mendapatkan pandangan cepat pasar <br>
    Tengah sesi 1   : 10:05 --> Informasi tambahan <br>
    Penutupan sesi 1: 11:35 --> persiapan sesi 2 <br>
    Pembukaan sesi 2: 13:35 --> mendapatkan pandangan cepat pasar <br>
    Penutupan sesi 2: 22:00 --> persiapan sesi besok <br>
    </p>

    <p><a href="https://github.com/venoajie/draf"> Source code</a> 

    </p>

    </body></html>
    """


    return html

def tabulasi ():

    '''
        Merapikan list saham dalam format keluaran yang disesuaikan dengan user: e mail/telegram/screen komputer

        Returns:           
            List saham dalam bentuk tabulasi menggunakan tabulate
    '''

    #! Modul untuk merapikan tabel	
    from tabulate import tabulate

#FIXME:
    #* menyiapkan isi e mail
    html=format_html()

    #! Menarik data yang sudah diekstraksi	
    result=ekstraksi_data()

    #* merapikan hasil dengan tabulate
    col_list=list(result.columns.values)
    keluaran = html.format(table=tabulate(result, headers=col_list, tablefmt="html",showindex=True))
#!	keluaran = html.format(table=tabulate(result, headers="keys", tablefmt="html",showindex=True)) --> alternatif, tanpa col list

    #* mengirimkan hasil satu per satu by telegram   
    my_message=  'Penarikan data selesai'
    (telegram_bot_sendtext(my_message)	    )

    #* mengirimkan hasil keseluruhan by e mail    
    print((send_mail(keluaran)))

    return result

#! eksekusi
(tabulasi())


