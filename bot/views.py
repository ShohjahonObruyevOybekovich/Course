# for user in users:
#     cert_count = Certification.objects.filter(
#         user=user, owner='Student',
#         created_at__range=(first_day, last_day)
#     ).count()
#
#     income = Bonus.objects.filter(
#         user=user, type="INCOME",
#         created_at__range=(first_day, last_day)
#     ).aggregate(Sum('amount'))['amount__sum'] or 0
#
#     expense = Bonus.objects.filter(
#         user=user, type="EXPENSE",
#         created_at__range=(first_day, last_day)
#     ).aggregate(Sum('amount'))['amount__sum'] or 0
#
#     event_count = Event.objects.filter(
#         user=user,
#         created_at__range=(first_day, last_day)
#     ).count()
#
#     data.append([
#         user.full_name or "Noma'lum",
#         user.phone or "Noma'lum",
#         f"{user.experience} yil" if user.experience else "Noma'lum",
#         f"{user.ball} ball",
#         cert_count,
#         f"{income} sum",
#         f"{expense} sum",
#         event_count
#     ])
#
# df = pd.DataFrame(data, columns=[
#     "Xodim ismi", "Telefon raqami", "Ish tajribasi",
#     "KPI ballari", "Sertifikatlar soni", "Bonus (sum)", "Xarajatlar (sum)", "Tadbirlar soni"
# ])
#
# output = io.BytesIO()
# with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
#     df.to_excel(writer, index=False, sheet_name="Xodimlar")
#
#     worksheet = writer.sheets["Xodimlar"]
#     header_format = writer.book.add_format({
#         'bold': True, 'bg_color': '#D7E4BC',
#         'text_wrap': True, 'align': 'center', 'valign': 'center', 'border': 1
#     })
#
#     for col_num, value in enumerate(df.columns.values):
#         worksheet.write(0, col_num, value, header_format)
#         worksheet.set_column(col_num, col_num, 20)
#
#     worksheet.freeze_panes(1, 0)
#
# output.seek(0)
# file_bytes = io.BytesIO(output.read())  # or just `output` directly
# filename = f"Xodimlar_{now.strftime('%Y-%m')}.xlsx"
# admins = User.objects.filter(role="ADMIN").all()
# for admin in admins:
#     if admin.chat_id:
#         bot.send_document(
#             chat_id=admin.chat_id,
#             file_bytes=file_bytes,
#             filename=filename,
#             caption=f"📊 {now.strftime('%Y-%m')} oyi uchun xodimlar hisoboti"
#         )
#         file_bytes.seek(0)  # Important: reset pointer for each new upload
# from django.shortcuts import render
#
# # Create your views here.
