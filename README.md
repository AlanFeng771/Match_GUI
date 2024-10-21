### Match GUI
#### Introduction
由於醫生提供的GT label 是 mask 的形式，因此我們需要將 mask 轉換成 bounding box 的形式，這樣才能進行訓練。我們使用3d cclabling演算法來將 mask 轉換成 bounding box 的形式。但由於mask是2d影像會發生連通性問題，因此會造成演算法無法正確的將mask轉換成bounding box。因此需要人工的方式去比對演算法轉換的bounding box是否正確。這個GUI的目的就是讓使用者可以比對演算法轉換的bounding box是否正確，並且可以進行修正。
以下我將醫生標記的GT label稱作 **nodule**，編號以醫生的標記檔**lung_M_class_0001-1800.xlsx**為準, 3d cclabling演算法轉換的bounding box稱作 **bbox**。這個程式的目的是讓使用者可以比對 nodule 和 bbox 的對應關係，包含類別、位置、大小等等，==主要以bbox對應的到為主==。
#### Question
目前根據統計nodule和bbox的對應會有幾種請況:
1. bbox和nodle的對應是一對一的關係
2. bbox和nodle的對應是多對一的關係
3. bbox和nodle的對應是一對多的關係

##### Analysis
1. bbox和nodle的對應是一對一的關係
    1. 這種情況是最理想的，代表演算法轉換的bbox是正確的。
2. bbox和nodle的對應是多對一的關係
    1. 因為mask是2d影像，slice之間的聯通性，導致演算法轉換的bbox會有多個(多個大個bbox)。這種情況需要人工的方式去比對，將對應的bbox合併成一個。
    2. 同一個slice同一個nodule會有多個bbox的情況(一個大的bbox，多個小bbox)，這種情況需要人工的方式去比對，刪除不正確的bbox。
3. bbox和nodle的對應是一對多的關係
    1. 這種情況是最不理想的，代表醫生可能將一個nodule分成兩個nodule去做標記。這種情況可能要請醫生確認

##### Example
1. 一個bbox對應到一個nodule
2. 多個bbox對應到一個nodule
    1. 以病人**0014**為例
    nodule 0, start slice->231
    ![alt text](image-3.png)
    bbox 0, slice->231-243
    ![alt text](image-4.png)
    bbox 1, slice->244-258
    ![alt text](image-5.png)
    >觀察 slice 243, 244可以發現mask不連續部分，導致bbox 0, bbox 1對應到同一個nodule
    ![alt text](image-6.png)
    ![alt text](image-7.png)
    2. 以病人**0256**為例
    nodule 0, start slice->163
    ![alt text](image-8.png)
    bbox 0, slice->163-172
    ![alt text](image-9.png)
    bbox 1, slice->170-172
    ![alt text](image-10.png)
    bbox 2, slice->167-169
    ![alt text](image-12.png)
    ![alt text](image-11.png)
    >可以發現bbox 0, bbox 1, bbox 2對應到同一個nodule，bbox 1, bbox 2明顯是錯誤的應該刪除
3. 一個bbox對應到多個nodule
    1. 以病人**0170**為例
    nodule 1, start slice->273
    ![alt text](image.png)
    nodule 0, start slice->276
    ![alt text](image-1.png)
    bbox 0, slice->270-278
    ![alt text](image-13.png)
    > 可以發現nodule 0, nodule 1應該被視為同一個
### GUI
#### 前置作業
請確保你具有以下的檔案:
1. lung_M_class_0001-1800.csv -> 醫生根據mask標記的資訊
2. Raw_npy/  -> 原始的dicom image 轉換成npy檔(沒有經過resample) (請從NAS自行下載 (BME\BME_dataset\Raw_npy))
    |--0001.npy
    |--0002.npy
    |--...
3. mask_npz/ -> GT mask 轉換成npz檔(沒有經過resample)
    |--0001.npz
    |--0002.npz
    |--...
4. bbox_annotation.csv -> 3d cclabling演算法轉換的bbox (patient_id,center_x,center_y,center_z,width,height,depth,type,index,is_checked)
5. patient_ids.txt -> 紀錄病人的ids (根據個人標記需求調整，gui會根據這個檔案的顯示需要標記的病人，不包含在內的病人不會顯示) 

#### 啟動GUI
- 請修改start.bat 正確的參數 (參考**前置作業**)
> output_file_name 可自行決定，這會決定輸出檔案的名稱 (ex: output_file_name.csv) 
- 執行start.bat
> 如果想要繼續標記請修改 start.bat 中的--bbox_annotation_file 參數，換成上一次輸出的檔案(ex: output_file_name.csv)
#### GUI介紹
![alt text](image-18.png)
- gui 分成兩個部分
    1. dicom image的顯示器
        1. 左邊的部分顯示nodule對應的dicom image，紅色的輪廓根據mask產生
        2. 右邊的部分顯示bbox對應的dicom image，矩形為bbox的位置
            1. 綠色的矩形代表目前選擇的bbox
            2. 紅色的矩形代表目前未被選擇的bbox

        ![alt text](image-19.png)
    2. nodules和bbox的控制元件
        1. 左邊的部分顯示nodule的資訊
            - 點選nodule id，顯示器左邊將會跳轉到對應的start slice
            > 因為式start slice，可以利用這個特性確定現在的nodule在mask上的位置，但是醫生標記的部分start slice是錯誤的。
        2. 右邊的部分顯示bbox的資訊
            - 點選bbox id，顯示器左邊將會跳轉到對應的start slice
            - 下方會同步顯示bbox的資訊(參考**使用方法**)

        ![alt text](image-20.png)
    3. Other
        1. next -> 下一個patient
        2. previous -> 上一個patient
        ![alt text](image-21.png)
        3. output -> 輸出目前的結果，記得結束標記一定要按下這個按鈕，不然會丟失標記的結果
        
#### 使用方式
我將bbox根據上面定義的問題應該要對應的操作分成四個部分:
1. Match-> 一個bbox對應到一個nodule
2. Combine-> 多個bbox合併成一個bbox
3. Delete-> 刪除不正確的bbox
4. Other-> 出現了沒有被定義的問題

##### Example
question 2.1
- 病人**0014**的bbox 0 應該和 bbox 1 合併
1. bbox 0 對應到 nodule 0
![alt text](image-14.png)
2. bbox 1 和 bbox 0 合併
![alt text](image-15.png)
> bbox 0 和 bbox 1 合併還是bbox 1 和 bbox 0 合併是一樣的
question 2.2
- 病人**0256**的bbox 1, bbox 2 應該刪除
1. bbox 0 對應到 nodule 0
![alt text](image-16.png)
2. bbox 1 和 bbox 2 刪除
![alt text](image-17.png)








