# Speaker Notes – Data Science Capstone Project Report

Short, simple English sentences with the Vietnamese translation.

## Slide 1 – Title

- Hello everyone. — *Xin chào mọi người.*
- My project is about SpaceX Falcon 9 rockets. — *Dự án của tôi nói về tên lửa SpaceX Falcon 9.*
- I want to predict if the first stage will land. — *Tôi muốn dự đoán tầng một có hạ cánh được không.*
- All my code is on GitHub. — *Toàn bộ code của tôi có trên GitHub.*

## Slide 2 – Project GitHub Repository

- This slide shows my GitHub repository. — *Slide này cho thấy kho GitHub của tôi.*
- Each step has its own notebook. — *Mỗi bước có một notebook riêng.*
- You can click the links to see the code. — *Bạn có thể bấm vào link để xem code.*

## Slide 3 – Outline

- This is the plan of my talk. — *Đây là kế hoạch bài trình bày của tôi.*
- First, the summary and the problem. — *Đầu tiên là tóm tắt và vấn đề.*
- Then methods, results, and conclusion. — *Sau đó là phương pháp, kết quả và kết luận.*

## Slide 4 – Executive Summary

- I collected real launch data from an API and Wikipedia. — *Tôi thu thập dữ liệu phóng thật từ API và Wikipedia.*
- Overall, 66.7% of first stages landed. — *Nhìn chung, 66.7% tầng một đã hạ cánh.*
- Landing success grew a lot over the years. — *Tỉ lệ hạ cánh thành công tăng rất nhiều qua các năm.*
- My best models reach 83.3% test accuracy. — *Các mô hình tốt nhất đạt độ chính xác 83.3% trên tập kiểm tra.*

## Slide 5 – Introduction

- SpaceX rockets cost about 62 million dollars. — *Tên lửa SpaceX có giá khoảng 62 triệu đô la.*
- Other companies cost 165 million dollars or more. — *Các công ty khác tốn 165 triệu đô la trở lên.*
- The big saving comes from reusing the first stage. — *Khoản tiết kiệm lớn đến từ việc tái sử dụng tầng một.*
- So we predict if the first stage will land. — *Vì vậy chúng tôi dự đoán tầng một có hạ cánh không.*

## Slide 6 – Data Collection – SpaceX API

- I call the SpaceX API to get past launches. — *Tôi gọi SpaceX API để lấy các lần phóng trước đây.*
- Then I look up rocket, pad, payload and core details. — *Sau đó tôi tra thông tin tên lửa, bệ phóng, tải trọng và lõi.*
- I keep only Falcon 9 and save a clean table. — *Tôi chỉ giữ Falcon 9 và lưu một bảng sạch.*

## Slide 7 – Data Collection – Web Scraping

- I download a Wikipedia page with launch tables. — *Tôi tải một trang Wikipedia có các bảng phóng.*
- BeautifulSoup reads the HTML tables. — *BeautifulSoup đọc các bảng HTML.*
- I get 121 launch rows and save them to CSV. — *Tôi lấy được 121 dòng và lưu vào CSV.*

## Slide 8 – Data Wrangling

- I check missing values first. — *Đầu tiên tôi kiểm tra giá trị bị thiếu.*
- Then I turn the landing outcome into a label called Class. — *Sau đó tôi biến kết quả hạ cánh thành nhãn tên là Class.*
- Class is 1 if the booster landed, and 0 if not. — *Class bằng 1 nếu tầng đẩy hạ cánh, bằng 0 nếu không.*
- The overall success rate is 66.7%. — *Tỉ lệ thành công tổng thể là 66.7%.*

## Slide 9 – EDA with Data Visualization

- I use charts to find patterns. — *Tôi dùng biểu đồ để tìm các quy luật.*
- Scatter plots show how two things relate. — *Biểu đồ phân tán cho thấy hai yếu tố liên quan thế nào.*
- A bar chart compares orbits, and a line chart shows the trend by year. — *Biểu đồ cột so sánh các quỹ đạo, biểu đồ đường cho thấy xu hướng theo năm.*

## Slide 10 – EDA with SQL

- I load the launch table into SQLite. — *Tôi nạp bảng phóng vào SQLite.*
- Then I answer ten questions with SQL. — *Sau đó tôi trả lời mười câu hỏi bằng SQL.*
- I use DISTINCT, LIKE, SUM, AVG, MIN, GROUP BY and subqueries. — *Tôi dùng DISTINCT, LIKE, SUM, AVG, MIN, GROUP BY và truy vấn con.*

## Slide 11 – Interactive Visual Analytics – Folium & Plotly Dash

- Folium puts every launch on a map. — *Folium đặt mỗi lần phóng lên bản đồ.*
- Green markers mean landed, red markers mean not landed. — *Điểm xanh là hạ cánh, điểm đỏ là không hạ cánh.*
- The Dash app lets users filter by site and payload. — *Ứng dụng Dash cho phép lọc theo bãi phóng và tải trọng.*

## Slide 12 – Predictive Analysis – Methodology

- I split the data into training and test sets. — *Tôi chia dữ liệu thành tập huấn luyện và tập kiểm tra.*
- I scale the features and tune four models. — *Tôi chuẩn hoá đặc trưng và tinh chỉnh bốn mô hình.*
- GridSearchCV finds the best settings with ten folds. — *GridSearchCV tìm thiết lập tốt nhất với mười phần.*
- Then I compare accuracy on the test set. — *Sau đó tôi so sánh độ chính xác trên tập kiểm tra.*

## Slide 13 – Flight Number vs. Payload Mass

- Each dot is one launch. — *Mỗi chấm là một lần phóng.*
- Green dots appear more on the right side. — *Chấm xanh xuất hiện nhiều hơn ở bên phải.*
- So SpaceX gets better with more flights. — *Vậy SpaceX tiến bộ hơn khi bay nhiều hơn.*

## Slide 14 – Flight Number vs. Launch Site

- CCAFS SLC 40 is used the most. — *CCAFS SLC 40 được dùng nhiều nhất.*
- Most early failures happened there. — *Phần lớn thất bại ban đầu xảy ra ở đó.*
- Later launches there are much better. — *Các lần phóng sau ở đó tốt hơn nhiều.*

## Slide 15 – Payload Mass vs. Launch Site

- Heavy payloads only fly from Florida. — *Tải nặng chỉ phóng từ Florida.*
- Vandenberg launches lighter payloads. — *Vandenberg phóng tải nhẹ hơn.*
- Heavy launches still land most of the time. — *Các lần phóng nặng vẫn hạ cánh phần lớn.*

## Slide 16 – Success Rate by Orbit Type

- Each bar is one orbit type. — *Mỗi cột là một loại quỹ đạo.*
- Some orbits have only one launch, so be careful. — *Một số quỹ đạo chỉ có một lần phóng, nên cần cẩn thận.*
- VLEO is high and GTO is low. — *VLEO cao còn GTO thấp.*

## Slide 17 – Flight Number vs. Orbit

- In LEO, success comes after a few flights. — *Ở LEO, thành công đến sau vài lần bay.*
- In GTO, there is no clear pattern. — *Ở GTO, không có quy luật rõ ràng.*
- VLEO launches started late and went well. — *Các lần phóng VLEO bắt đầu muộn và diễn ra tốt.*

## Slide 18 – Payload Mass vs. Orbit

- Heavy payloads to VLEO are fine. — *Tải nặng lên VLEO thì ổn.*
- Heavy payloads to GTO are harder. — *Tải nặng lên GTO thì khó hơn.*
- GTO needs more fuel, so less is left for landing. — *GTO cần nhiều nhiên liệu, nên còn ít để hạ cánh.*

## Slide 19 – Launch Success Yearly Trend

- This line shows the success rate each year. — *Đường này cho thấy tỉ lệ thành công mỗi năm.*
- It goes up strongly after 2013. — *Nó tăng mạnh sau năm 2013.*
- SpaceX learned quickly. — *SpaceX học hỏi rất nhanh.*

## Slide 20 – SQL Results: Launch Sites

- There are four launch sites in the table. — *Có bốn bãi phóng trong bảng.*
- Three are in Florida and one is in California. — *Ba bãi ở Florida và một bãi ở California.*
- The first five CCA records are early flights. — *Năm bản ghi CCA đầu tiên là các chuyến bay sớm.*

## Slide 21 – SQL Results: Payloads

- NASA CRS missions carried about forty-five thousand kilograms in total. — *Các sứ mệnh NASA CRS mang tổng cộng khoảng bốn mươi lăm nghìn kg.*
- F9 v1.1 carried about two thousand nine hundred kilograms on average. — *F9 v1.1 mang trung bình khoảng hai nghìn chín trăm kg.*
- Only Block 5 boosters carried the maximum payload. — *Chỉ các tầng đẩy Block 5 mang tải tối đa.*

## Slide 22 – SQL Results: Success Rates

- Almost every mission reached orbit. — *Hầu như mọi sứ mệnh đều lên quỹ đạo.*
- Only one mission failed in flight. — *Chỉ có một sứ mệnh thất bại khi bay.*
- Four boosters landed on a drone ship with medium payloads. — *Bốn tầng đẩy hạ cánh trên tàu không người lái với tải trung bình.*

## Slide 23 – SQL Results: Ranking Landing Outcomes

- This query ranks landing outcomes in the early years. — *Truy vấn này xếp hạng kết quả hạ cánh trong những năm đầu.*
- No attempt is the most common result. — *Không thử hạ cánh là kết quả phổ biến nhất.*
- Drone ship success and failure are equal. — *Thành công và thất bại trên tàu không người lái bằng nhau.*

## Slide 24 – SQL Results: Time Analysis

- The first ground pad landing was in December 2015. — *Lần hạ cánh trên bệ mặt đất đầu tiên là tháng 12 năm 2015.*
- In 2015, two drone ship landings failed. — *Năm 2015, có hai lần hạ cánh trên tàu thất bại.*
- They were in January and April. — *Chúng xảy ra vào tháng 1 và tháng 4.*

## Slide 25 – Folium: All Launch Sites on the Map

- Here are all four launch sites. — *Đây là bốn bãi phóng.*
- They are close to the coast. — *Chúng nằm gần bờ biển.*
- They are also in the south, near the equator. — *Chúng cũng ở phía nam, gần xích đạo.*

## Slide 26 – Folium: Launch Outcomes per Site

- Each marker is one launch. — *Mỗi điểm đánh dấu là một lần phóng.*
- Green means landed and red means not landed. — *Xanh nghĩa là hạ cánh, đỏ nghĩa là không hạ cánh.*
- KSC LC-39A has the most green markers. — *KSC LC-39A có nhiều điểm xanh nhất.*

## Slide 27 – Folium: Proximity Analysis (CCAFS SLC-40)

- I measure distances from the launch site. — *Tôi đo khoảng cách từ bãi phóng.*
- The coast and railway are very close. — *Bờ biển và đường sắt rất gần.*
- The city is far away for safety. — *Thành phố ở xa để đảm bảo an toàn.*

## Slide 28 – Dash: Successful Launches by Site (All Sites)

- This pie shows where the successful launches come from. — *Biểu đồ tròn này cho thấy các lần thành công đến từ đâu.*
- KSC LC-39A has the biggest share. — *KSC LC-39A có phần lớn nhất.*
- CCAFS SLC-40 has the smallest share. — *CCAFS SLC-40 có phần nhỏ nhất.*

## Slide 29 – Dash: Highest Success Rate Site – KSC LC-39A

- This pie is only for KSC LC-39A. — *Biểu đồ tròn này chỉ dành cho KSC LC-39A.*
- 76.9% of its launches were successful. — *76.9% số lần phóng ở đây thành công.*
- It is the best site in this data. — *Đây là bãi phóng tốt nhất trong dữ liệu này.*

## Slide 30 – Dash: Payload vs. Launch Outcome (All Sites)

- These charts show payload and outcome together. — *Các biểu đồ này cho thấy tải trọng và kết quả cùng nhau.*
- Light and medium payloads succeed more often. — *Tải nhẹ và trung bình thành công thường xuyên hơn.*
- The FT booster version has the best success rate. — *Phiên bản tầng đẩy FT có tỉ lệ thành công tốt nhất.*

## Slide 31 – Classification Accuracy

- I tested four models. — *Tôi đã thử bốn mô hình.*
- Three models tie at 83.3% on the test set. — *Ba mô hình hoà nhau ở mức 83.3% trên tập kiểm tra.*
- SVM has the best validation score. — *SVM có điểm kiểm định tốt nhất.*
- The decision tree is the weakest on the test set. — *Cây quyết định yếu nhất trên tập kiểm tra.*

## Slide 32 – Confusion Matrix

- The test set has 18 launches. — *Tập kiểm tra có 18 lần phóng.*
- All landed boosters are predicted correctly by three models. — *Ba mô hình dự đoán đúng tất cả tầng đẩy đã hạ cánh.*
- The problem is false positives. — *Vấn đề là dương tính giả.*
- Some failed landings are predicted as landed. — *Một số lần hạ cánh thất bại bị dự đoán là đã hạ cánh.*

## Slide 33 – Best Model

- On the test set, three models are equal. — *Trên tập kiểm tra, ba mô hình bằng nhau.*
- The test set is small, so this tie is not surprising. — *Tập kiểm tra nhỏ nên việc hoà không có gì lạ.*
- SVM is a little better in cross validation. — *SVM tốt hơn một chút khi kiểm định chéo.*
- So I choose SVM, but the difference is small. — *Vì vậy tôi chọn SVM, nhưng khác biệt là nhỏ.*

## Slide 34 – What Really Drives Landing Success?

- 21 of the 30 failures were not real failures. — *21 trong 30 lần thất bại không phải thất bại thật.*
- SpaceX did not even try to land. — *SpaceX thậm chí không thử hạ cánh.*
- When they tried, 87% landed. — *Khi họ thử, 87% đã hạ cánh.*
- So the key question is: will they try to land? — *Vậy câu hỏi chính là: họ có thử hạ cánh không?*

## Slide 35 – Conclusion

- SpaceX improved very fast over the years. — *SpaceX tiến bộ rất nhanh qua các năm.*
- Orbit, payload and experience affect landing. — *Quỹ đạo, tải trọng và kinh nghiệm ảnh hưởng đến hạ cánh.*
- Our models predict landing with about eighty-three percent accuracy. — *Mô hình của chúng tôi dự đoán hạ cánh với độ chính xác khoảng tám mươi ba phần trăm.*
- My advice: first predict if SpaceX will try to land. — *Lời khuyên của tôi: hãy dự đoán trước SpaceX có thử hạ cánh không.*

## Slide 36 – Appendix: Data Sources and Notes

- This slide lists my data sources. — *Slide này liệt kê các nguồn dữ liệu của tôi.*
- The SpaceX API was down, so I used saved copies of the same data. — *SpaceX API bị lỗi nên tôi dùng bản lưu của cùng dữ liệu đó.*
- Everything is in the GitHub repository. — *Mọi thứ đều có trong kho GitHub.*

