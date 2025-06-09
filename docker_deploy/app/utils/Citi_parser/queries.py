
url = "https://www.citilink.ru/graphql/"

PRODUCTS_QUERY = """query GetSubcategoryProductsFilter($subcategoryProductsFilterInput:CatalogFilter_ProductsFilterInput!,$categoryFilterInput:Catalog_CategoryFilterInput!,$categoryCompilationFilterInput:Catalog_CategoryCompilationFilterInput!){productsFilter(filter:$subcategoryProductsFilterInput){record{...SubcategoryProductsFilter},error{... on CatalogFilter_ProductsFilterInternalError{__typename,message},... on CatalogFilter_ProductsFilterIncorrectArgumentsError{__typename,message}}},category(filter:$categoryFilterInput){...SubcategoryCategoryInfo}}fragment SubcategoryProductsFilter on CatalogFilter_ProductsFilter{__typename,products{...ProductSnippetFull},sortings{id,name,slug,directions{id,isSelected,name,slug,isDefault}},groups{...SubcategoryProductsFilterGroup},compilations{popular{...SubcategoryProductCompilationInfo},brands{...SubcategoryProductCompilationInfo},carousel{...SubcategoryProductCompilationInfo}},pageInfo{...Pagination},searchStrategy}fragment ProductSnippetFull on Catalog_Product{...ProductSnippetShort,propertiesShort{...ProductProperty},rating,counters{opinions,reviews}}fragment ProductSnippetShort on Catalog_Product{...ProductSnippetBase,labels{...ProductLabel},delivery{__typename,self{__typename,availabilityByDays{__typename,deliveryTime,storeCount},availableInFavoriteStores{store{id,shortName},productsCount}}},stock{countInStores,maxCountInStock},yandexPay{withYandexSplit}}fragment ProductSnippetBase on Catalog_Product{id,name,shortName,slug,isAvailable,images{citilink{...Image}},price{...ProductPrice},category{id,name},brand{name},multiplicity,quantityInPackageFromSupplier}fragment Image on Image{sources{url,size}}fragment ProductPrice on Catalog_ProductPrice{current,old,club,clubPriceViewType,discount{percent}}fragment ProductLabel on Catalog_Label{id,type,title,description,target{...Target},textColor,backgroundColor,expirationTime}fragment Target on Catalog_Target{action{...TargetAction},url,inNewWindow}fragment TargetAction on Catalog_TargetAction{id}fragment ProductProperty on Catalog_Property{name,value}fragment SubcategoryProductsFilterGroup on CatalogFilter_FilterGroup{id,isCollapsed,isDisabled,name,filter{... on CatalogFilter_ListFilter{__typename,isSearchable,logic,filters{id,isDisabled,isInShortList,isInTagList,isSelected,name,total,childGroups{id,isCollapsed,isDisabled,name,filter{... on CatalogFilter_ListFilter{__typename,isSearchable,logic,filters{id,isDisabled,isInShortList,isInTagList,name,isSelected,total}},... on CatalogFilter_RangeFilter{__typename,fromValue,isInTagList,maxValue,minValue,serifValues,scaleStep,toValue,unit}}}}},... on CatalogFilter_RangeFilter{__typename,fromValue,isInTagList,maxValue,minValue,serifValues,scaleStep,toValue,unit}}}fragment SubcategoryProductCompilationInfo on CatalogFilter_CompilationInfo{__typename,compilation{...SubcategoryProductCompilation},isSelected}fragment SubcategoryProductCompilation on Catalog_ProductCompilation{__typename,id,type,name,slug,parentSlug,seo{h1,title,text,description}}fragment Pagination on PageInfo{hasNextPage,hasPreviousPage,perPage,page,totalItems,totalPages}fragment SubcategoryCategoryInfo on Catalog_CategoryResult{... on Catalog_Category{...Category,seo{h1,title,text,description},compilation(filter:$categoryCompilationFilterInput){... on Catalog_CategoryCompilation{__typename,id,name,seo{h1,title,description,text}},... on Catalog_CategoryCompilationIncorrectArgumentError{__typename,message},... on Catalog_CategoryCompilationNotFoundError{__typename,message}},defaultSnippetType},... on Catalog_CategoryIncorrectArgumentError{__typename,message},... on Catalog_CategoryNotFoundError{__typename,message}}fragment Category on Catalog_Category{__typename,id,name,slug}"""

PROPERTIES_QUERY = """query GetProductTabProperties($filter:Catalog_ProductFilterInput!){product(filter:$filter){...ProductTabProperties}}fragment ProductTabProperties on Catalog_Product{propertiesGroup{...PropertyGroup}}fragment PropertyGroup on Catalog_PropertyGroup{id,name,properties{...Property}}fragment Property on Catalog_Property{id,name,description,value,measure}"""

DOCUMENTS_QUERY = """query GetProductTabDocumentation($filter:Catalog_ProductFilterInput!){product(filter:$filter){...ProductTabDocumentation}}fragment ProductTabDocumentation on Catalog_Product{documentation{certificates{...Document},attachments{...Document}}}fragment Document on Catalog_ProductDocument{size,title,url}"""

RATING_QUERY = """query($filter1:Catalog_ProductFilterInput!$input2:UGC_OpinionsInput!){product_b6304_d984e:product(filter:$filter1){opinions_03450_55993:opinions(input:$input2){payload{summary{rating ratingCounters{__typename count percentage rating}bestOpinion{id creationDate pros cons text rating isBest author{id b2c{__typename ...on B2C_PublicUserNotFoundError{message}...on B2C_PublicUserB2C{id userInfo{nickname firstName avatar{sources{__typename url size}}}expert{isExpert}}}counters{__typename ...on B2C_UserActivityCountersNotFoundError{message}...on B2C_UserActivityCounters{review opinion question}}vendor{__typename ...on B2C_VendorNotFoundError{message}...on B2C_Vendor{brand{id name}categories{__typename id}}}}status vendor voteInfo{info{type counters{likes dislikes}isVoted}target{id}}authorNickname abuse{reasons{__typename id name targetType isMessageRequired withMessage}target}}}items{__typename id creationDate pros cons text rating isBest author{id b2c{__typename ...on B2C_PublicUserNotFoundError{message}...on B2C_PublicUserB2C{id userInfo{nickname firstName avatar{sources{__typename url size}}}expert{isExpert}}}counters{__typename ...on B2C_UserActivityCountersNotFoundError{message}...on B2C_UserActivityCounters{review opinion question}}vendor{__typename ...on B2C_VendorNotFoundError{message}...on B2C_Vendor{brand{id name}categories{__typename id}}}}status vendor voteInfo{info{type counters{likes dislikes}isVoted}target{id}}authorNickname abuse{reasons{__typename id name targetType isMessageRequired withMessage}target}}sortings{__typename id name sort isSelected}}pageInfo{page perPage totalItems totalPages hasNextPage hasPreviousPage}}}}"""

REVIEW_QUERY = """query($filter1:Catalog_ProductFilterInput!$input2:UGC_ReviewsInput!){product_b6304_839cf:product(filter:$filter1){reviews_b6834_ed052:reviews(input:$input2){items{__typename id content_84701_bf21a:content title viewsCount author{id b2c{__typename ...on B2C_PublicUserNotFoundError{message}...on B2C_PublicUserB2C{id userInfo{nickname firstName avatar{sources{__typename url size}}}expert{isExpert}}}counters{__typename ...on B2C_UserActivityCountersNotFoundError{message}...on B2C_UserActivityCounters{review opinion question}}vendor{__typename ...on B2C_VendorNotFoundError{message}...on B2C_Vendor{brand{id name}categories{__typename id}}}}status vendor voteInfo{info{type counters{likes dislikes}isVoted}target{id}}isBlocked creationDate}pageInfo{page perPage totalItems totalPages hasNextPage hasPreviousPage}}}}"""

def PRODUCT_VARIABLE(category, current_page_products):
    return {
        "subcategoryProductsFilterInput": {
            "categorySlug": category,
            "compilationPath": [],
            "pagination": {
                "page": current_page_products,
                "perPage": 48,
            },
            "conditions": [],
            "sorting": {
                "id": "",
                "direction": "SORT_DIRECTION_DESC",
            },
            "popularitySegmentId": "THREE",
        },
        "categoryFilterInput": {
            "slug": category,
        },
        "categoryCompilationFilterInput": {
            "slug": "",
        },
    }

def PROPERTIES_OR_DOCUMENTS_VARIABLE(product_id):
    return {
        "filter": {
            "id": product_id,
        }
    }

def RATING_VARIABLE(product_id, current_page_rating):
    return {
        "filter1": {
            "id": product_id
        },
        "input2": {
            "pagination": {
                "page": current_page_rating,
                "perPage": 5
            }
        }
    }

def REVIEW_VARIABLE(product_id, current_page_review):
    return {
        "filter1": {
            "id": product_id
        },
        "input2": {
            "pagination": {
                "page": current_page_review,
                "perPage": 4
            },
            "forCurrentUser": False,
        }
    }

