<template>
  <div class="book">
    <h2>{{ title }}</h2>
    <div class="buttons">
      <div class="btn">
        <a
          :href="`http://localhost:8000/book/download?book_id=${id}`"
          :download="`${id}.txt`"
          @click.prevent="handleDownload"
        >
          <img src="~/assets/images/download.svg" alt="Скачать" class="icon" />
        </a>
      </div>

      <div class="btn">
        <button @click="handleDelete" class="delete-btn">
          <img src="~/assets/images/delete.svg" alt="Удалить" class="icon" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'

const props = defineProps({
  id: {
    type: Number,
    required: true
  },
  title: {
    type: String,
    required: true
  }
})

async function handleDownload() {
  try {
    const res = await fetch(`http://localhost:8000/book/download?book_id=${props.id}`);
    if (!res.ok) {
      throw new Error(`Ошибка скачивания: ${res.status}`);
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${props.id}.txt`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
  } catch (e) {
    console.error(e);
    alert('Не удалось скачать книгу.');
  }
}

async function handleDelete() {
  if (!confirm('Вы уверены, что хотите удалить эту книгу?')) return;

  try {
    const res = await fetch(`http://localhost:8000/book/delete?book_id=${props.id}`, {
      method: 'DELETE'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail?.[0]?.msg || `HTTP ${res.status}`);
    }
    const data = await res.json();
    if (data.ok) {
      alert('Книга удалена.');
      // Чтобы обновить список книг, можно эмитировать событие или использовать composables (например, emit('deleted', id))
      // Например: emit('deleted', props.id);
    } else {
      throw new Error('Удаление не подтверждено сервером.');
    }
  } catch (e) {
    console.error(e);
    alert('Не удалось удалить книгу: ' + e.message);
  }
}
</script>

