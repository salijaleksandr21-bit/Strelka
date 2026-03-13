<template>
    <div class="book">
        <h2><slot name="title" /></h2>
        <p>
            Дата загрузки: <slot name="date" /><br>
            Размер текста: <slot name="size" /> MB<br>
            Выделено разделов: <slot name="section" /> шт<br>
        </p>
        <div class="buttons">
            <div class="btn">
                n
            </div>
            <div class="btn">
                n
            </div>
        </div>
    </div>
</template>